"""RAG 1 Domain Knowledge Service implementation."""
import logging
from typing import List, Optional

from app.data.models import (
    KnowledgeChunk,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchHit,
    RAGHealthResponse,
    RAGEvidence
)
from app.data.ingestion import ingest_knowledge_base
from app.core.language import detect_language
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector import VectorRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.synthesizer import build_evidence_list, synthesize_answer_context
from app.config import settings

from app.data.storage import storage

logger = logging.getLogger(__name__)


class RAG1Service:
    """
    RAG 1 Domain Service encapsulates the Ayurveda + Intellectual Property
    knowledge repository and hybrid retrieval pipeline.
    """

    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.vector_retriever: Optional[VectorRetriever] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self._is_ready: bool = False

    def initialize(self) -> None:
        """Loads knowledge dataset from vector.db (or raw files if first run) and fits retrieval indices."""
        logger.info("Initializing RAG 1 Knowledge Base...")
        
        if storage.is_initialized():
            logger.info(f"Loading knowledge base from existing vector.db ({storage.db_path})...")
            self.chunks = storage.load_chunks()
        else:
            logger.info(f"vector.db not found or empty. Ingesting raw dataset files...")
            self.chunks = ingest_knowledge_base()

        self.bm25_retriever = BM25Retriever().fit(self.chunks)
        self.vector_retriever = VectorRetriever().fit(self.chunks)
        self.hybrid_retriever = HybridRetriever(self.bm25_retriever, self.vector_retriever)

        # Persist to vector.db if not already saved
        if not storage.is_initialized() and self.chunks:
            logger.info("Saving chunks and embeddings into vector.db for standalone deployment...")
            embeddings_dict = self.vector_retriever.get_chunk_embeddings_dict()
            storage.save_knowledge_base(self.chunks, embeddings_dict)

        self._is_ready = True
        logger.info(f"RAG 1 initialized successfully with {len(self.chunks)} chunks (vector.db ready).")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Executes query answering conforming to POST /api/v1/rag/knowledge/query.
        """
        if not self._is_ready:
            raise RuntimeError("RAG 1 service is not yet initialized.")

        query_text = request.query.strip()
        lang = request.language or detect_language(query_text)
        top_k = request.top_k or settings.DEFAULT_TOP_K

        # Retrieve top hits via hybrid search
        hits = self.hybrid_retriever.search(
            query=query_text,
            mode="hybrid",
            domain_filter=request.domain,
            top_k=len(self.chunks) if request.jurisdiction else top_k
        )

        if request.jurisdiction:
            allowed = {"INDIA", "NATIONAL (INDIA)"} if request.jurisdiction == "INDIA" else {"INTERNATIONAL"}
            hits = [(chunk, score) for chunk, score in hits if (chunk.jurisdiction or "").upper() in allowed][:top_k]

        evidence = build_evidence_list(hits)
        top_score = hits[0][1] if hits else 0.0
        answer_context = synthesize_answer_context(query_text, evidence, lang)

        return RAGQueryResponse(
            query=query_text,
            language=lang,
            answer_context=answer_context,
            evidence=evidence,
            retrieval_score=round(top_score, 4)
        )

    def search(self, request: RAGSearchRequest) -> RAGSearchResponse:
        """
        Executes granular search conforming to POST /api/v1/rag/knowledge/search.
        Supports 'hybrid', 'vector', and 'bm25' modes.
        """
        if not self._is_ready:
            raise RuntimeError("RAG 1 service is not yet initialized.")

        query_text = request.query.strip()
        mode = (request.mode or "hybrid").lower()
        top_k = request.top_k or settings.DEFAULT_TOP_K

        hits = self.hybrid_retriever.search(
            query=query_text,
            mode=mode,
            domain_filter=request.domain,
            top_k=top_k
        )

        results: List[RAGSearchHit] = []
        for chunk, score in hits:
            results.append(
                RAGSearchHit(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    domain=chunk.domain,
                    subtopic=chunk.topic,
                    text=chunk.text,
                    source_name=chunk.source_name,
                    source_url=chunk.source_url,
                    score=round(score, 4),
                    retrieval_method=mode
                )
            )

        return RAGSearchResponse(
            query=query_text,
            mode=mode,
            total_hits=len(results),
            results=results
        )

    def health(self) -> RAGHealthResponse:
        """
        Returns status conforming to GET /api/v1/rag/knowledge/health.
        """
        domains = list(set(c.domain for c in self.chunks)) if self.chunks else []
        sources = list(set(c.source_name for c in self.chunks)) if self.chunks else []

        return RAGHealthResponse(
            status="healthy" if self._is_ready else "uninitialized",
            rag_id="RAG1_AYURVEDA_IP",
            total_chunks=len(self.chunks),
            total_sources=len(sources),
            domains_indexed=sorted(domains),
            retrievers_active=["bm25_okapi", "vector_sublinear_tfidf", "reciprocal_rank_fusion"]
        )


# Global singleton instance
rag1_service = RAG1Service()
