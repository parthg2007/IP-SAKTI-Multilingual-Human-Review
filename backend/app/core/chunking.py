"""Semantic chunking and canonical metadata builder."""
import hashlib
from typing import Dict, Any, List
from app.data.models import KnowledgeChunk
from app.core.language import detect_language


def generate_content_hash(text: str) -> str:
    """Computes SHA-256 hash of chunk text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def map_domain_to_canonical(raw_domain: str, subtopic: str = "") -> str:
    """Normalizes raw domain into standard canonical domain category."""
    raw = (raw_domain or "").strip()
    sub = (subtopic or "").strip()

    if "Prior Art" in raw or "Classical" in raw:
        return "Prior Art & Classical Literature"
    elif "Patent" in raw or "IPR" in raw:
        return "Patents & IPR Procedures"
    elif "Statutory" in raw or "Act" in raw:
        return "Statutory Law"
    elif "Benefit" in raw or "ABS" in raw or "Biodiversity" in raw:
        return "Access & Benefit Sharing (ABS)"
    elif "Ayurveda" in sub or "Ayurveda" in raw:
        return "AYURVEDA"
    return raw or "GENERAL_DOMAIN"


def build_chunk_from_record(record: Dict[str, Any], index: int) -> KnowledgeChunk:
    """
    Transforms a raw dataset record into a fully enriched KnowledgeChunk
    conforming to README.MD specifications.
    """
    chunk_num = index + 1
    chunk_id = f"RAG1-{chunk_num:06d}"
    record_id = record.get("record_id", f"REC-{chunk_num:04d}")
    
    # Generate deterministic document ID based on source and subtopic
    source_name = record.get("source_name", "Official AYUSH/IP Source")
    subtopic = record.get("subtopic") or ""
    raw_domain = record.get("domain", "")
    domain = map_domain_to_canonical(raw_domain, subtopic)
    
    # Compute document ID
    doc_seed = f"{source_name}_{domain}_{subtopic}".lower().replace(" ", "_")
    doc_hash = hashlib.md5(doc_seed.encode("utf-8")).hexdigest()[:6].upper()
    document_id = f"DOC-{doc_hash}"

    text = record.get("text", "").strip()
    language = record.get("language") or detect_language(text)

    # Subdomain extraction
    subdomain = None
    if "Form I" in subtopic or "Rule 14" in subtopic:
        subdomain = "ABS_PROCEDURES"
    elif "Classical" in domain or "TKRC" in subtopic:
        subdomain = "CLASSICAL_LITERATURE"
    elif "Section 3" in subtopic or "Patent" in domain:
        subdomain = "PATENTABILITY"
    elif "Section 6" in subtopic or "Section 40" in subtopic:
        subdomain = "BIODIVERSITY_STATUTE"

    return KnowledgeChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        record_id=record_id,
        domain=domain,
        subdomain=subdomain or record.get("subdomain"),
        topic=subtopic or record.get("topic"),
        jurisdiction=record.get("jurisdiction", "National (India)"),
        language=language,
        title=record.get("title", f"Knowledge Item {chunk_num}"),
        text=text,
        source_name=source_name,
        source_url=record.get("source_url"),
        authority_tier=record.get("authority_tier", "auxiliary_seed"),
        rag_role=record.get("rag_role", "domain_context"),
        formulation_category=record.get("formulation_category"),
        document_version="1.0",
        published_at=record.get("published_at"),
        content_hash=generate_content_hash(text),
        note=record.get("note")
    )
