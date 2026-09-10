"""Hybrid retrieval engine combining BM25 keyword and dense vector search via RRF."""
from typing import List, Dict, Tuple, Optional
from app.data.models import KnowledgeChunk, RAGSearchHit
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector import VectorRetriever
from app.core.language import detect_language, normalize_and_expand_query
from app.config import settings


class HybridRetriever:
    """
    Hybrid retriever implementing:
    1. Language detection & query normalization / expansion
    2. Parallel BM25 and Dense Vector search
    3. Reciprocal Rank Fusion (RRF) & Weighted Score Combination
    4. Domain boost reranking
    """

    def __init__(self, bm25_retriever: BM25Retriever, vector_retriever: VectorRetriever):
        self.bm25 = bm25_retriever
        self.vector = vector_retriever
        self.rrf_k = settings.RRF_K
        self.bm25_weight = settings.HYBRID_BM25_WEIGHT
        self.vector_weight = settings.HYBRID_VECTOR_WEIGHT

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        domain_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Retrieves top_k chunks using the specified mode (hybrid, vector, or bm25).
        """
        # Step 1: Language detection and query expansion
        expanded_query, matched_concepts, suggested_domains = normalize_and_expand_query(query)

        # If user didn't specify a domain filter, but a domain was strongly suggested by terminology
        active_domain = domain_filter
        if not active_domain and suggested_domains and len(suggested_domains) == 1:
            active_domain = suggested_domains[0]

        # Mode dispatch
        if mode == "bm25":
            return self.bm25.search(expanded_query, active_domain, top_k)
        elif mode == "vector":
            return self.vector.search(expanded_query, active_domain, top_k)

        # Step 2: Hybrid search (Vector + BM25)
        # Retrieve candidate pools from both
        candidate_pool_size = max(top_k * 3, 20)
        bm25_hits = self.bm25.search(expanded_query, active_domain, candidate_pool_size)
        vec_hits = self.vector.search(expanded_query, active_domain, candidate_pool_size)

        # Step 3: Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, KnowledgeChunk] = {}

        # Add BM25 ranks
        for rank, (chunk, raw_score) in enumerate(bm25_hits, start=1):
            chunk_map[chunk.chunk_id] = chunk
            score = self.bm25_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + score

        # Add Vector ranks
        for rank, (chunk, raw_score) in enumerate(vec_hits, start=1):
            chunk_map[chunk.chunk_id] = chunk
            score = self.vector_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + score

        # Step 4: Concept boost reranking
        for chunk_id, chunk in chunk_map.items():
            boost = 1.0
            for concept in matched_concepts:
                if concept.lower() in chunk.title.lower() or concept.lower() in chunk.text.lower():
                    boost += 0.15
            rrf_scores[chunk_id] = rrf_scores[chunk_id] * boost

        # Sort descending
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Normalize top score to a calibrated 0.0 - 1.0 range
        if sorted_chunks:
            max_score = sorted_chunks[0][1]
            results = [
                (chunk_map[cid], round(min(1.0, (score / max_score) * 0.95), 4))
                for cid, score in sorted_chunks[:top_k]
            ]
        else:
            # Fallback if both returned empty
            results = []

        return results
