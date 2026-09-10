"""SQLite-based vector_rag2.db persistence for RAG 2 legal chunks and dense vectors.
Provides self-contained, lightning-fast offline operation with zero external DB dependencies.
"""
import sqlite3
import struct
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from app.rag2.models import LegalEvidenceChunk
from app.config import settings

logger = logging.getLogger(__name__)


def serialize_vector(vec: np.ndarray) -> bytes:
    """Serializes a 1D float array to binary blob for high-speed storage in SQLite."""
    vec_flat = np.asarray(vec, dtype=np.float32).flatten()
    return struct.pack(f"{len(vec_flat)}f", *vec_flat)


def deserialize_vector(blob: bytes) -> np.ndarray:
    """Deserializes binary blob from SQLite into a 1D float32 numpy array."""
    num_floats = len(blob) // 4
    floats = struct.unpack(f"{num_floats}f", blob)
    return np.array(floats, dtype=np.float32)


class LegalVectorDBStorage:
    """
    Manages the local vector_rag2.db SQLite database file.
    Stores statutory chunks, extracted sections/rules, versioning, and dense vectors.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or getattr(settings, "RAG2_VECTOR_DB_PATH", Path("vector_rag2.db"))

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self) -> None:
        """Initializes tables and indexes in vector_rag2.db."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_chunks (
                    record_id TEXT PRIMARY KEY,
                    chunk_id TEXT,
                    document_id TEXT,
                    category TEXT,
                    domain TEXT,
                    document_type TEXT,
                    document_title TEXT,
                    source_url TEXT,
                    jurisdiction TEXT,
                    authority_tier TEXT,
                    rag_role TEXT,
                    section TEXT,
                    rule TEXT,
                    article TEXT,
                    version TEXT,
                    effective_from TEXT,
                    effective_to TEXT,
                    status TEXT,
                    language TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    content_hash TEXT,
                    source_corpus TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_legal_category ON legal_chunks(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_legal_document ON legal_chunks(document_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_legal_domain ON legal_chunks(domain)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_legal_section ON legal_chunks(section)
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    dim INTEGER,
                    vector_blob BLOB,
                    FOREIGN KEY(chunk_id) REFERENCES legal_chunks(chunk_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def is_initialized(self) -> bool:
        """Checks if vector_rag2.db exists and contains records."""
        if not self.db_path.exists():
            return False
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as cnt FROM legal_chunks")
            row = cursor.fetchone()
            return bool(row and row["cnt"] > 0)
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

    def save_knowledge_base(
        self,
        chunks: List[LegalEvidenceChunk],
        chunk_embeddings: Optional[Dict[str, np.ndarray]] = None
    ) -> None:
        """Saves legal chunks and vectors into vector_rag2.db."""
        self.init_tables()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for ch in chunks:
                cursor.execute("""
                    INSERT OR REPLACE INTO legal_chunks (
                        record_id, chunk_id, document_id, category, domain,
                        document_type, document_title, source_url, jurisdiction,
                        authority_tier, rag_role, section, rule, article,
                        version, effective_from, effective_to, status,
                        language, chunk_index, text, content_hash, source_corpus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ch.record_id, ch.chunk_id, ch.document_id, ch.category, ch.domain,
                    ch.document_type, ch.document_title, ch.source_url, ch.jurisdiction,
                    ch.authority_tier, ch.rag_role, ch.section, ch.rule, ch.article,
                    ch.version, ch.effective_from, ch.effective_to, ch.status,
                    ch.language, ch.chunk_index, ch.text, ch.content_hash, ch.source_corpus
                ))

            if chunk_embeddings:
                for chunk_id, vec in chunk_embeddings.items():
                    blob = serialize_vector(vec)
                    dim = len(vec)
                    cursor.execute("""
                        INSERT OR REPLACE INTO legal_embeddings (chunk_id, dim, vector_blob)
                        VALUES (?, ?, ?)
                    """, (chunk_id, dim, blob))

            cursor.execute("""
                INSERT OR REPLACE INTO legal_metadata (key, value) VALUES ('total_chunks', ?)
            """, (str(len(chunks)),))
            conn.commit()
            logger.info(f"Saved {len(chunks)} legal chunks to {self.db_path}")
        finally:
            conn.close()

    def load_chunks(self) -> List[LegalEvidenceChunk]:
        """Loads all legal chunks from vector_rag2.db."""
        if not self.db_path.exists():
            return []

        chunks: List[LegalEvidenceChunk] = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM legal_chunks ORDER BY chunk_index ASC")
            for row in cursor.fetchall():
                ch = LegalEvidenceChunk(
                    record_id=row["record_id"],
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    category=row["category"],
                    domain=row["domain"],
                    document_type=row["document_type"],
                    document_title=row["document_title"],
                    source_url=row["source_url"],
                    jurisdiction=row["jurisdiction"],
                    authority_tier=row["authority_tier"],
                    rag_role=row["rag_role"],
                    section=row["section"],
                    rule=row["rule"],
                    article=row["article"],
                    version=row["version"],
                    effective_from=row["effective_from"],
                    effective_to=row["effective_to"],
                    status=row["status"],
                    language=row["language"] or "en",
                    chunk_index=row["chunk_index"],
                    text=row["text"],
                    content_hash=row["content_hash"],
                    source_corpus=row["source_corpus"]
                )
                chunks.append(ch)
            return chunks
        finally:
            conn.close()

    def load_embeddings(self) -> Tuple[List[str], Optional[np.ndarray]]:
        """Loads embeddings matrix and corresponding chunk_ids from vector_rag2.db."""
        if not self.db_path.exists():
            return [], None

        chunk_ids = []
        vectors = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, vector_blob FROM legal_embeddings ORDER BY chunk_id ASC")
            for row in cursor.fetchall():
                chunk_ids.append(row["chunk_id"])
                vectors.append(deserialize_vector(row["vector_blob"]))

            if not vectors:
                return chunk_ids, None

            return chunk_ids, np.vstack(vectors)
        finally:
            conn.close()


# Global RAG 2 storage instance
legal_storage = LegalVectorDBStorage()
