"""Standalone builder script to generate/populate vector.db from datasets.
Can be executed as a pre-build step on Render or run locally.
"""
import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data.ingestion import ingest_knowledge_base
from app.retrieval.vector import VectorRetriever
from app.data.storage import storage

from app.rag2.ingestion import ingest_legal_knowledge_base
from app.rag2.retrieval import LegalVectorRetriever
from app.rag2.storage import legal_storage


def build():
    print("==================================================")
    print("1. Building RAG 1 (Ayurveda + IP Domain Knowledge)...")
    print(f"Target DB Path: {storage.db_path}")
    print("==================================================")

    chunks1 = ingest_knowledge_base()
    print(f"Ingested {len(chunks1)} knowledge chunks from RAG 1 dataset.")

    print("Computing semantic vectors for RAG 1...")
    vec1 = VectorRetriever().fit(chunks1)
    storage.save_knowledge_base(chunks1, vec1.get_chunk_embeddings_dict())

    loaded1 = storage.load_chunks()
    print(f"RAG 1 Verification: Loaded {len(loaded1)} chunks from {storage.db_path}.")

    print("\n==================================================")
    print("2. Building RAG 2 (Authoritative Legal & Regulatory Evidence)...")
    print(f"Target DB Path: {legal_storage.db_path}")
    print("==================================================")

    chunks2 = ingest_legal_knowledge_base()
    print(f"Ingested {len(chunks2)} authoritative legal chunks from RAG 2 dataset.")

    print("Computing semantic vectors for RAG 2...")
    vec2 = LegalVectorRetriever().fit(chunks2)
    legal_storage.save_knowledge_base(chunks2, vec2.get_chunk_embeddings_dict())

    loaded2 = legal_storage.load_chunks()
    chunk_ids2, _ = legal_storage.load_embeddings()
    print(f"RAG 2 Verification: Loaded {len(loaded2)} chunks and {len(chunk_ids2)} vectors from {legal_storage.db_path}.")
    print("\nBuild complete! Both vector.db and vector_rag2.db are ready.")


if __name__ == "__main__":
    build()

