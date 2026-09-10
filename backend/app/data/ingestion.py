"""Data ingestion module for loading, parsing, deduplicating, and enriching domain records."""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.data.models import KnowledgeChunk
from app.core.chunking import build_chunk_from_record, generate_content_hash

logger = logging.getLogger(__name__)


def load_source_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """Loads source manifest for source metadata and authority tiers."""
    path = manifest_path or settings.DATA_MANIFEST_PATH
    manifest: Dict[str, Dict[str, str]] = {}
    if not path.exists():
        logger.warning(f"Manifest file not found at {path}")
        return manifest

    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_name = row.get("source_name", "").strip()
                if source_name:
                    manifest[source_name] = {
                        "source_url": row.get("source_url", "").strip(),
                        "authority_tier": row.get("authority_tier", "auxiliary_seed").strip(),
                        "note": row.get("note", "").strip()
                    }
    except Exception as e:
        logger.error(f"Failed to load source manifest: {e}")

    return manifest


def load_raw_records_from_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Reads raw records from JSONL file."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON line: {e}")
    return records


def load_raw_records_from_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Reads raw records from CSV file."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def ingest_knowledge_base() -> List[KnowledgeChunk]:
    """
    Ingests and validates knowledge base records from JSONL (preferred) or CSV.
    Performs cleaning, deduplication, metadata enrichment, and chunking.
    """
    manifest = load_source_manifest()
    raw_records: List[Dict[str, Any]] = []

    if settings.DATA_JSONL_PATH.exists():
        logger.info(f"Ingesting records from JSONL: {settings.DATA_JSONL_PATH}")
        raw_records = load_raw_records_from_jsonl(settings.DATA_JSONL_PATH)
    elif settings.DATA_CSV_PATH.exists():
        logger.info(f"Ingesting records from CSV fallback: {settings.DATA_CSV_PATH}")
        raw_records = load_raw_records_from_csv(settings.DATA_CSV_PATH)
    else:
        raise FileNotFoundError(
            f"No knowledge dataset found at {settings.DATA_JSONL_PATH} or {settings.DATA_CSV_PATH}"
        )

    chunks: List[KnowledgeChunk] = []
    seen_hashes = set()
    seen_record_ids = set()

    for idx, record in enumerate(raw_records):
        text = record.get("text", "").strip()
        record_id = record.get("record_id", "").strip()
        if not text:
            continue

        content_hash = generate_content_hash(text)
        # Deduplication check
        if content_hash in seen_hashes or (record_id and record_id in seen_record_ids):
            continue

        seen_hashes.add(content_hash)
        if record_id:
            seen_record_ids.add(record_id)

        # Merge manifest metadata if missing
        source_name = record.get("source_name", "").strip()
        if source_name in manifest:
            m_info = manifest[source_name]
            if not record.get("source_url") and m_info.get("source_url"):
                record["source_url"] = m_info["source_url"]
            if not record.get("authority_tier") and m_info.get("authority_tier"):
                record["authority_tier"] = m_info["authority_tier"]
            if not record.get("note") and m_info.get("note"):
                record["note"] = m_info["note"]

        chunk = build_chunk_from_record(record, len(chunks))
        chunks.append(chunk)

    logger.info(f"Successfully ingested {len(chunks)} unique knowledge chunks.")
    return chunks
