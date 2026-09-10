"""Version-aware and historical point-in-time legal validity engine for RAG 2."""
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from app.rag2.models import LegalEvidenceChunk

logger = logging.getLogger(__name__)


def parse_date_str(date_str: str) -> Optional[datetime]:
    """Parses date string supporting YYYY-MM-DD, YYYY-MM, or YYYY."""
    if not date_str:
        return None
    d = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(d, fmt)
        except ValueError:
            continue
    return None


def is_chunk_applicable_at_date(chunk: LegalEvidenceChunk, requested_date: str) -> Tuple[bool, str]:
    """
    Evaluates whether a statutory chunk was legally in force at a given historical date.
    Returns: (is_applicable, rationale)
    """
    req_dt = parse_date_str(requested_date)
    if not req_dt:
        return True, "Invalid date format; defaulting to applicable."

    # Effective from check
    eff_from_dt = parse_date_str(chunk.effective_from) if chunk.effective_from else None
    if eff_from_dt and req_dt < eff_from_dt:
        return (
            False,
            f"Not yet in force on {requested_date}. Provision enacted on {chunk.effective_from} ({chunk.document_title})."
        )

    # Effective to check
    eff_to_dt = parse_date_str(chunk.effective_to) if chunk.effective_to else None
    if eff_to_dt and req_dt > eff_to_dt:
        return (
            False,
            f"Repealed or superseded before {requested_date}. Provision ceased on {chunk.effective_to} ({chunk.document_title})."
        )

    return True, f"Authoritative and in force as of {requested_date}."


def filter_by_historical_date(
    chunks: List[Tuple[LegalEvidenceChunk, float]],
    requested_date: str
) -> Tuple[List[Tuple[LegalEvidenceChunk, float]], List[Tuple[LegalEvidenceChunk, str]]]:
    """
    Filters retrieved chunks by historical date.
    Returns: (applicable_hits, inapplicable_hits_with_reason)
    """
    applicable = []
    inapplicable = []

    for chunk, score in chunks:
        is_app, reason = is_chunk_applicable_at_date(chunk, requested_date)
        if is_app:
            applicable.append((chunk, score))
        else:
            inapplicable.append((chunk, reason))

    return applicable, inapplicable
