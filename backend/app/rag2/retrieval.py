"""High-precision hybrid retrieval engine (BM25 + Dense Semantic Vectors) for RAG 2."""
import math
import re
import logging
from collections import Counter
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.rag2.models import LegalEvidenceChunk
from app.config import settings

logger = logging.getLogger(__name__)

LEGAL_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:\([a-z0-9]+\))?|\w+", re.UNICODE)


def tokenize_legal_text(text: str) -> List[str]:
    """Tokenizes legal text while preserving section/subsection tokens like '3(p)', '3(e)', etc."""
    tokens = []
    for match in LEGAL_TOKEN_PATTERN.finditer(text.lower()):
        tok = match.group(0)
        if len(tok) > 1 or tok.isalnum():
            tokens.append(tok)
    return tokens


class LegalBM25Retriever:
    """Okapi BM25 sparse keyword retriever tuned for legal citations and statutory text."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[LegalEvidenceChunk] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}

    def fit(self, chunks: List[LegalEvidenceChunk]) -> "LegalBM25Retriever":
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_len = []
        self.doc_freqs = Counter()
        self.inverted_index = {}

        for doc_idx, chunk in enumerate(chunks):
            # Boost header / section metadata in document token stream
            extra_tokens = []
            if chunk.section:
                extra_tokens.extend([chunk.section.lower(), f"section {chunk.section.lower()}", f"sec {chunk.section.lower()}"] * 3)
            if chunk.rule:
                extra_tokens.extend([chunk.rule.lower(), f"rule {chunk.rule.lower()}"] * 3)
            if chunk.article:
                extra_tokens.extend([chunk.article.lower(), f"article {chunk.article.lower()}"] * 3)
            if chunk.category:
                extra_tokens.extend([chunk.category.lower().replace("_", " ")] * 2)

            full_text = f"{chunk.document_title} {' '.join(extra_tokens)} {chunk.text}"
            tokens = tokenize_legal_text(full_text)
            self.doc_len.append(len(tokens))

            counts = Counter(tokens)
            for token, freq in counts.items():
                self.doc_freqs[token] += 1
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((doc_idx, freq))

        self.avg_doc_len = sum(self.doc_len) / max(1, self.corpus_size)

        for token, df in self.doc_freqs.items():
            self.idf[token] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

        logger.info(f"Fitted LegalBM25 with {self.corpus_size} chunks and {len(self.idf)} unique terms.")
        return self

    def search(
        self,
        query: str,
        category_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        jurisdiction_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[LegalEvidenceChunk, float]]:
        q_tokens = tokenize_legal_text(query)
        if not q_tokens:
            return []

        scores: Dict[int, float] = {}
        for token in q_tokens:
            if token not in self.inverted_index:
                continue
            idf = self.idf.get(token, 0.0)
            for doc_idx, freq in self.inverted_index[token]:
                dl = self.doc_len[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_doc_len))
                term_score = idf * (numerator / denominator)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + term_score

        scored_list = []
        for doc_idx, score in scores.items():
            chunk = self.chunks[doc_idx]
            if category_filter and chunk.category.lower() != category_filter.lower():
                continue
            if domain_filter and chunk.domain.lower() != domain_filter.lower():
                continue
            if jurisdiction_filter and chunk.jurisdiction.lower() != jurisdiction_filter.lower():
                continue
            scored_list.append((chunk, score))

        scored_list.sort(key=lambda x: x[1], reverse=True)
        return scored_list[:top_k]


class LegalVectorRetriever:
    """Dense semantic retriever using sublinear n-gram representations."""

    def __init__(self):
        self.chunks: List[LegalEvidenceChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.embeddings: Optional[np.ndarray] = None
        self.chunk_ids: List[str] = []

    def fit(self, chunks: List[LegalEvidenceChunk]) -> "LegalVectorRetriever":
        self.chunks = chunks
        self.chunk_ids = [c.chunk_id for c in chunks]

        corpus = []
        for c in chunks:
            extra = f"{c.document_title} {c.category} {c.section or ''} {c.rule or ''} {c.article or ''}"
            corpus.append(f"{extra} {c.text}")

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            sublinear_tf=True,
            ngram_range=(1, 2),
            max_features=12000,
            norm="l2"
        )
        self.embeddings = self.vectorizer.fit_transform(corpus).toarray().astype(np.float32)
        logger.info(f"Fitted LegalVectorRetriever: shape={self.embeddings.shape}")
        return self

    def load_precomputed(self, chunks: List[LegalEvidenceChunk], chunk_ids: List[str], embeddings: np.ndarray) -> "LegalVectorRetriever":
        self.chunks = chunks
        self.chunk_ids = chunk_ids
        self.embeddings = embeddings.astype(np.float32)
        # Refit vectorizer for query transformation
        corpus = [f"{c.document_title} {c.category} {c.section or ''} {c.text}" for c in chunks]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            sublinear_tf=True,
            ngram_range=(1, 2),
            max_features=self.embeddings.shape[1],
            norm="l2"
        )
        self.vectorizer.fit(corpus)
        return self

    def get_chunk_embeddings_dict(self) -> Dict[str, np.ndarray]:
        if self.embeddings is None:
            return {}
        return {cid: self.embeddings[idx] for idx, cid in enumerate(self.chunk_ids)}

    def search(
        self,
        query: str,
        category_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        jurisdiction_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[LegalEvidenceChunk, float]]:
        if self.vectorizer is None or self.embeddings is None or not self.chunks:
            return []

        q_vec = self.vectorizer.transform([query]).toarray().astype(np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = np.dot(self.embeddings, q_vec.T).flatten()

        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            if category_filter and chunk.category.lower() != category_filter.lower():
                continue
            if domain_filter and chunk.domain.lower() != domain_filter.lower():
                continue
            if jurisdiction_filter and chunk.jurisdiction.lower() != jurisdiction_filter.lower():
                continue
            results.append((chunk, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class LegalHybridRetriever:
    """Reciprocal Rank Fusion hybrid engine combining BM25 and Dense Vector search."""

    def __init__(self, bm25: LegalBM25Retriever, vector: LegalVectorRetriever):
        self.bm25 = bm25
        self.vector = vector
        self.k_rrf = settings.RRF_K
        self.w_bm25 = settings.HYBRID_BM25_WEIGHT
        self.w_vector = settings.HYBRID_VECTOR_WEIGHT

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        category_filter: Optional[str] = None,
        domain_filter: Optional[str] = None,
        jurisdiction_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[LegalEvidenceChunk, float]]:
        cand_k = max(top_k * 4, 30)

        if mode == "bm25":
            return self.bm25.search(query, category_filter, domain_filter, jurisdiction_filter, top_k)
        if mode == "vector":
            return self.vector.search(query, category_filter, domain_filter, jurisdiction_filter, top_k)

        # Hybrid Reciprocal Rank Fusion
        bm25_hits = self.bm25.search(query, category_filter, domain_filter, jurisdiction_filter, cand_k)
        vec_hits = self.vector.search(query, category_filter, domain_filter, jurisdiction_filter, cand_k)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, LegalEvidenceChunk] = {}

        for rank, (chunk, _) in enumerate(bm25_hits):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.w_bm25 / (self.k_rrf + rank + 1))

        for rank, (chunk, _) in enumerate(vec_hits):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.w_vector / (self.k_rrf + rank + 1))

        # Legal Section / Article priority reranker
        q_lower = query.lower()
        sec_mentions = re.findall(r"\b(?:section|sec|धारा)?\s*([0-9]+[a-z]?(?:\([a-z0-9]+\))?)\b", q_lower)

        final_list: List[Tuple[LegalEvidenceChunk, float]] = []
        for cid, base_score in rrf_scores.items():
            chunk = chunk_map[cid]
            boost = 1.0

            # Direct section match boost
            if chunk.section and any(m in chunk.section.lower() or chunk.section.lower() in m for m in sec_mentions):
                boost *= 2.2
            if chunk.rule and any(m in chunk.rule.lower() for m in sec_mentions):
                boost *= 1.8
            if chunk.article and any(m in chunk.article.lower() for m in sec_mentions):
                boost *= 2.0

            final_list.append((chunk, base_score * boost))

        final_list.sort(key=lambda x: x[1], reverse=True)
        return final_list[:top_k]
