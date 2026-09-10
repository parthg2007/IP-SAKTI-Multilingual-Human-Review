"""RAG 2 Legal & Regulatory Evidence service implementation."""
import logging
from typing import List, Optional, Dict, Any, Tuple

from app.rag2.models import (
    LegalEvidenceChunk,
    LegalQueryRequest,
    LegalQueryResponse,
    HistoricalQueryRequest,
    HistoricalQueryResponse,
    LegalSearchRequest,
    LegalSearchResponse,
    LegalSearchHit,
    RAG2HealthResponse
)
from app.rag2.ingestion import ingest_legal_knowledge_base
from app.rag2.storage import legal_storage
from app.rag2.retrieval import LegalBM25Retriever, LegalVectorRetriever, LegalHybridRetriever
from app.rag2.normalizer import normalize_legal_query
from app.rag2.versioning import filter_by_historical_date
from app.rag2.conflict import conflict_engine
from app.rag2.synthesizer import build_legal_citations, synthesize_legal_answer_context
from app.core.language import detect_language
from app.config import settings

logger = logging.getLogger(__name__)


class RAG2Service:
    """
    RAG 2 Service encapsulates the authoritative Legal and Regulatory Evidence
    repository, hybrid statutory retrieval, historical versioning, and conflict detection.
    """

    def __init__(self):
        self.chunks: List[LegalEvidenceChunk] = []
        self.bm25_retriever: Optional[LegalBM25Retriever] = None
        self.vector_retriever: Optional[LegalVectorRetriever] = None
        self.hybrid_retriever: Optional[LegalHybridRetriever] = None
        self._is_ready: bool = False

    def initialize(self) -> None:
        """Initializes RAG 2 by loading from vector_rag2.db or ingesting raw dataset."""
        logger.info("Initializing RAG 2 Legal & Regulatory Knowledge Base...")

        if legal_storage.is_initialized():
            logger.info(f"Loading legal chunks from existing vector_rag2.db ({legal_storage.db_path})...")
            self.chunks = legal_storage.load_chunks()
        else:
            logger.info("vector_rag2.db not found. Ingesting raw legal JSONL dataset...")
            self.chunks = ingest_legal_knowledge_base()

        self.bm25_retriever = LegalBM25Retriever().fit(self.chunks)
        self.vector_retriever = LegalVectorRetriever().fit(self.chunks)
        self.hybrid_retriever = LegalHybridRetriever(self.bm25_retriever, self.vector_retriever)

        # Persist to vector_rag2.db if first run
        if not legal_storage.is_initialized() and self.chunks:
            logger.info("Persisting legal chunks and vectors into vector_rag2.db...")
            embeddings_dict = self.vector_retriever.get_chunk_embeddings_dict()
            legal_storage.save_knowledge_base(self.chunks, embeddings_dict)

        self._is_ready = True
        logger.info(f"RAG 2 initialized successfully with {len(self.chunks)} authoritative legal chunks.")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def query(self, request: LegalQueryRequest) -> LegalQueryResponse:
        """Executes authoritative legal query conforming to POST /api/v1/rag/legal/query."""
        if not self._is_ready:
            raise RuntimeError("RAG 2 service is not yet initialized.")

        raw_query = request.query.strip()
        lang = request.language or detect_language(raw_query)

        # Multilingual normalization and concept expansion
        expanded_query, suggested_cat, matched_concepts = normalize_legal_query(raw_query)
        cat_filter = request.categories[0] if request.categories else suggested_cat
        if not request.categories and cat_filter and request.jurisdiction:
            # An inferred Indian category must not exclude the international treaty corpus.
            if not any(c.category == cat_filter and c.jurisdiction.upper() == request.jurisdiction.upper() for c in self.chunks):
                cat_filter = None
                expanded_query = raw_query
        domain_filter = request.domains[0] if request.domains else None
        top_k = request.top_k or settings.DEFAULT_TOP_K

        # Retrieve candidate legal chunks via hybrid search
        hits = self.hybrid_retriever.search(
            query=expanded_query,
            mode="hybrid",
            category_filter=cat_filter,
            domain_filter=domain_filter,
            jurisdiction_filter=request.jurisdiction,
            top_k=top_k * 2 if request.as_of_date else top_k
        )

        # Apply historical / as-of-date filtering if requested
        if request.as_of_date:
            hits, _ = filter_by_historical_date(hits, request.as_of_date)
            hits = hits[:top_k]

        candidate_chunks = [c for c, _ in hits]
        rag_evidences, legal_citations = build_legal_citations(hits)

        # Check for statutory tensions or conflicts
        conflict_found, conflict_expl = (False, None)
        if request.jurisdiction == "INDIA":
            conflict_found, conflict_expl = conflict_engine.check_conflicts(candidate_chunks, raw_query)

        # Synthesize answer context
        answer_context = synthesize_legal_answer_context(raw_query, legal_citations, candidate_chunks, lang)
        if conflict_found and conflict_expl:
            answer_context += f"\n\n[Statutory Qualification / Conflict Resolution]:\n{conflict_expl}"

        retrieval_meta = {
            "method": "hybrid_rrf",
            "reranked": True,
            "matched_concepts": matched_concepts,
            "total_candidates": len(hits)
        }

        return LegalQueryResponse(
            query=raw_query,
            jurisdiction=request.jurisdiction or "INDIA",
            language=lang,
            answer_context=answer_context,
            evidence=rag_evidences,
            citations=legal_citations,
            retrieval_metadata=retrieval_meta,
            conflict_detected=conflict_found,
            conflict_details=conflict_expl
        )

    def historical_query(self, request: HistoricalQueryRequest) -> HistoricalQueryResponse:
        """Executes point-in-time statutory check conforming to POST /api/v1/rag/legal/historical."""
        if not self._is_ready:
            raise RuntimeError("RAG 2 service is not yet initialized.")

        query_text = request.query.strip()
        top_k = request.top_k or 5

        hits = self.hybrid_retriever.search(
            query=query_text,
            category_filter=request.category,
            top_k=top_k * 2
        )

        applicable_hits, inapplicable_hits = filter_by_historical_date(hits, request.requested_date)
        applicable_hits = applicable_hits[:top_k]

        rag_evs, citations = build_legal_citations(applicable_hits)
        is_current = bool(applicable_hits)

        if applicable_hits:
            explanation = (
                f"As of {request.requested_date}, {len(applicable_hits)} statutory provisions were active and in force. "
                f"Primary governing enactment: {applicable_hits[0][0].document_title}."
            )
        else:
            reason = inapplicable_hits[0][1] if inapplicable_hits else "No applicable statutes found."
            explanation = f"Statutory bar or enactment mismatch on {request.requested_date}: {reason}"

        return HistoricalQueryResponse(
            query=query_text,
            requested_date=request.requested_date,
            is_current_law=is_current,
            applicable_provisions=citations,
            evidence=rag_evs,
            explanation=explanation
        )

    def search(self, request: LegalSearchRequest) -> LegalSearchResponse:
        """Executes granular statutory search conforming to POST /api/v1/rag/legal/search."""
        if not self._is_ready:
            raise RuntimeError("RAG 2 service is not yet initialized.")

        mode = (request.mode or "hybrid").lower()
        top_k = request.top_k or 10

        hits = self.hybrid_retriever.search(
            query=request.query.strip(),
            mode=mode,
            category_filter=request.category,
            domain_filter=request.domain,
            jurisdiction_filter=request.jurisdiction,
            top_k=top_k
        )

        results = []
        for chunk, score in hits:
            results.append(
                LegalSearchHit(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.document_title,
                    category=chunk.category,
                    domain=chunk.domain,
                    section=chunk.section,
                    rule=chunk.rule,
                    article=chunk.article,
                    text=chunk.text,
                    source_url=chunk.source_url,
                    authority_tier=chunk.authority_tier,
                    score=round(score, 4),
                    retrieval_method=mode
                )
            )

        return LegalSearchResponse(
            query=request.query,
            mode=mode,
            total_hits=len(results),
            results=results
        )

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieves document overview and chunks for a given document_id."""
        doc_chunks = [c for c in self.chunks if c.document_id.lower() == document_id.lower() or c.category.lower() == document_id.lower()]
        if not doc_chunks:
            return {"error": f"Document ID '{document_id}' not found."}

        first = doc_chunks[0]
        return {
            "document_id": first.document_id,
            "title": first.document_title,
            "category": first.category,
            "domain": first.domain,
            "jurisdiction": first.jurisdiction,
            "authority_tier": first.authority_tier,
            "source_url": first.source_url,
            "total_chunks": len(doc_chunks),
            "sample_chunk": {
                "chunk_id": first.chunk_id,
                "section": first.section,
                "rule": first.rule,
                "text": first.text[:400]
            }
        }

    def health(self) -> RAG2HealthResponse:
        """Returns health metrics conforming to GET /api/v1/rag/legal/health."""
        categories = sorted(list(set(c.category for c in self.chunks))) if self.chunks else []
        domains = sorted(list(set(c.domain for c in self.chunks))) if self.chunks else []

        return RAG2HealthResponse(
            status="healthy" if self._is_ready else "uninitialized",
            rag_id="RAG2_LEGAL_REGULATORY",
            total_chunks=len(self.chunks),
            categories_indexed=categories,
            domains_indexed=domains,
            retrievers_active=["bm25_legal", "vector_sublinear_tfidf", "reciprocal_rank_fusion", "section_reranker"]
        )


# Global singleton instance
rag2_service = RAG2Service()
