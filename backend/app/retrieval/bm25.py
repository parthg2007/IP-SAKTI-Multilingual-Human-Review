"""BM25 Okapi sparse keyword retrieval engine."""
import math
import re
from collections import Counter
from typing import List, Dict, Tuple, Optional
from app.data.models import KnowledgeChunk
from app.config import settings

# Common English and transliterated stopwords
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "this", "or", "what", "how", "why", "which", "where", "who",
    "kya", "hai", "kaise", "ke", "liye", "mein", "ka", "ki", "ko", "se"
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into alphanumeric/Unicode words, preserving technical terms."""
    if not text:
        return []
    # Match words in English, Hindi/Devanagari, and numbers/hyphenated terms
    tokens = re.findall(r"[\w]+", text.lower(), re.UNICODE)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Retriever:
    """Okapi BM25 implementation for domain keyword retrieval."""

    def __init__(self, k1: float = None, b: float = None):
        self.k1 = k1 if k1 is not None else settings.BM25_K1
        self.b = b if b is not None else settings.BM25_B
        self.chunks: List[KnowledgeChunk] = []
        self.corpus_size: int = 0
        self.avgdl: float = 0.0
        self.doc_lengths: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_token_counts: List[Counter] = []

    def fit(self, chunks: List[KnowledgeChunk]) -> "BM25Retriever":
        """Index the knowledge chunks."""
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_token_counts = []
        self.doc_lengths = []
        self.doc_freqs = {}

        total_length = 0
        for chunk in chunks:
            # Combine title, topic, domain, and text for rich indexing
            full_text = f"{chunk.title} {chunk.topic or ''} {chunk.domain} {chunk.subdomain or ''} {chunk.text}"
            tokens = tokenize(full_text)
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)

            counts = Counter(tokens)
            self.doc_token_counts.append(counts)

            for token in counts.keys():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avgdl = (total_length / self.corpus_size) if self.corpus_size > 0 else 0.0

        # Calculate IDF for each token
        for token, freq in self.doc_freqs.items():
            # BM25+ / Robertson IDF
            self.idf[token] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

        return self

    def search(
        self,
        query: str,
        domain_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Executes BM25 search over indexed chunks.
        Returns list of (KnowledgeChunk, score) sorted descending.
        """
        if not self.chunks or not query:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[Tuple[int, float]] = []

        for idx, chunk in enumerate(self.chunks):
            # Optional domain filtering
            if domain_filter:
                filter_lower = domain_filter.strip().lower()
                chunk_domain_lower = chunk.domain.lower()
                if filter_lower not in chunk_domain_lower and chunk_domain_lower not in filter_lower:
                    continue

            score = 0.0
            doc_len = self.doc_lengths[idx]
            counts = self.doc_token_counts[idx]

            for token in query_tokens:
                if token not in counts:
                    continue
                tf = counts[token]
                idf = self.idf.get(token, 0.0)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avgdl or 1.0)))
                score += idf * (numerator / denominator)

            if score > 0.0:
                scores.append((idx, score))

        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)

        results = [(self.chunks[idx], score) for idx, score in scores[:top_k]]
        return results
