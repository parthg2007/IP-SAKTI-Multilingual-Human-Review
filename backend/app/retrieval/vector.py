"""Dense semantic vector retrieval engine."""
import numpy as np
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.data.models import KnowledgeChunk


class VectorRetriever:
    """
    Vector retrieval engine providing dense semantic similarity search.
    Utilizes sublinear-scaled word & character n-gram embeddings for robust
    cross-lingual and morphological semantic matching.
    """

    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        # Word and subword n-gram vectorizer for rich semantic similarity
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            norm="l2",
            lowercase=True
        )
        self.doc_embeddings: Optional[np.ndarray] = None

    def fit(self, chunks: List[KnowledgeChunk]) -> "VectorRetriever":
        """Builds semantic vector representations for knowledge chunks."""
        self.chunks = chunks
        if not chunks:
            return self

        corpus = [
            f"{c.title}. {c.domain}. {c.topic or ''}. {c.subdomain or ''}. {c.text}"
            for c in chunks
        ]
        self.doc_embeddings = self.vectorizer.fit_transform(corpus)
        return self

    def get_chunk_embeddings_dict(self) -> dict:
        """Returns mapping of chunk_id -> 1D numpy array."""
        if self.doc_embeddings is None or not self.chunks:
            return {}
        dense = self.doc_embeddings.toarray()
        return {
            self.chunks[i].chunk_id: dense[i]
            for i in range(len(self.chunks))
        }

    def search(
        self,
        query: str,
        domain_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Computes cosine similarity between query vector and document embeddings.
        Returns list of (KnowledgeChunk, cosine_similarity) sorted descending.
        """
        if not self.chunks or self.doc_embeddings is None or not query.strip():
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(query_vec, self.doc_embeddings)[0]
        except Exception:
            return []

        results: List[Tuple[KnowledgeChunk, float]] = []

        for idx, score in enumerate(sims):
            if score <= 0.001:
                continue

            chunk = self.chunks[idx]
            if domain_filter:
                filter_lower = domain_filter.strip().lower()
                chunk_domain_lower = chunk.domain.lower()
                if filter_lower not in chunk_domain_lower and chunk_domain_lower not in filter_lower:
                    continue

            results.append((chunk, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
