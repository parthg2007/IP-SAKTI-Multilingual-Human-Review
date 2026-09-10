"""SQLite-based vector.db persistence for metadata and semantic vectors.
Enables standalone operation on Render without requiring external SQL servers.
"""
import sqlite3
import struct
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from app.data.models import KnowledgeChunk
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


class VectorDBStorage:
    """
    Manages the local vector.db SQLite database file.
    Stores chunk records, authority metadata, and precomputed semantic vectors.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or getattr(settings, "VECTOR_DB_PATH", Path("vector.db"))

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self) -> None:
        """Initializes tables in vector.db."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    record_id TEXT,
                    domain TEXT,
                    subdomain TEXT,
                    topic TEXT,
                    jurisdiction TEXT,
                    language TEXT,
                    title TEXT,
                    text TEXT,
                    source_name TEXT,
                    source_url TEXT,
                    authority_tier TEXT,
                    rag_role TEXT,
                    formulation_category TEXT,
                    document_version TEXT,
                    published_at TEXT,
                    content_hash TEXT,
                    note TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    dim INTEGER,
                    vector_blob BLOB,
                    FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def is_initialized(self) -> bool:
        """Checks if vector.db exists and contains records."""
        if not self.db_path.exists():
            return False
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as cnt FROM chunks")
            row = cursor.fetchone()
            return bool(row and row["cnt"] > 0)
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

    def save_knowledge_base(
        self,
        chunks: List[KnowledgeChunk],
        chunk_embeddings: Optional[Dict[str, np.ndarray]] = None
    ) -> None:
        """Saves knowledge chunks and their vectors to vector.db."""
        self.init_tables()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for chunk in chunks:
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks (
                        chunk_id, document_id, record_id, domain, subdomain, topic,
                        jurisdiction, language, title, text, source_name, source_url,
                        authority_tier, rag_role, formulation_category, document_version,
                        published_at, content_hash, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.chunk_id, chunk.document_id, chunk.record_id, chunk.domain,
                    chunk.subdomain, chunk.topic, chunk.jurisdiction, chunk.language,
                    chunk.title, chunk.text, chunk.source_name, chunk.source_url,
                    chunk.authority_tier, chunk.rag_role, chunk.formulation_category,
                    chunk.document_version, chunk.published_at, chunk.content_hash,
                    chunk.note
                ))

            if chunk_embeddings:
                for chunk_id, vec in chunk_embeddings.items():
                    blob = serialize_vector(vec)
                    dim = len(vec)
                    cursor.execute("""
                        INSERT OR REPLACE INTO embeddings (chunk_id, dim, vector_blob)
                        VALUES (?, ?, ?)
                    """, (chunk_id, dim, blob))

            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value) VALUES ('total_chunks', ?)
            """, (str(len(chunks)),))
            conn.commit()
            logger.info(f"Saved {len(chunks)} chunks to {self.db_path}")
        finally:
            conn.close()

    def load_chunks(self) -> List[KnowledgeChunk]:
        """Loads all chunks from vector.db."""
        if not self.db_path.exists():
            return []

        chunks: List[KnowledgeChunk] = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks ORDER BY chunk_id ASC")
            for row in cursor.fetchall():
                chunk = KnowledgeChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    record_id=row["record_id"],
                    domain=row["domain"],
                    subdomain=row["subdomain"],
                    topic=row["topic"],
                    jurisdiction=row["jurisdiction"],
                    language=row["language"] or "en",
                    title=row["title"],
                    text=row["text"],
                    source_name=row["source_name"],
                    source_url=row["source_url"],
                    authority_tier=row["authority_tier"],
                    rag_role=row["rag_role"],
                    formulation_category=row["formulation_category"],
                    document_version=row["document_version"],
                    published_at=row["published_at"],
                    content_hash=row["content_hash"],
                    note=row["note"]
                )
                chunks.append(chunk)
            return chunks
        finally:
            conn.close()

    def load_embeddings(self) -> Tuple[List[str], Optional[np.ndarray]]:
        """Loads embeddings matrix and corresponding chunk_ids from vector.db."""
        if not self.db_path.exists():
            return [], None

        chunk_ids = []
        vectors = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, vector_blob FROM embeddings ORDER BY chunk_id ASC")
            for row in cursor.fetchall():
                chunk_ids.append(row["chunk_id"])
                vectors.append(deserialize_vector(row["vector_blob"]))

            if not vectors:
                return chunk_ids, None

            return chunk_ids, np.vstack(vectors)
        finally:
            conn.close()


# Global storage instance
storage = VectorDBStorage()
