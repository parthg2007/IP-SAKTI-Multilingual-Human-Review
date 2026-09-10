"""Ingestion, parsing, and enrichment pipeline for RAG 2 (Legal & Regulatory Evidence)."""
import csv
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.rag2.models import LegalEvidenceChunk

logger = logging.getLogger(__name__)

# Map raw categories to canonical statutory Document IDs and enactment metadata
DOCUMENT_METADATA_MAP: Dict[str, Dict[str, Any]] = {
    "patents_act": {
        "document_id": "PATENTS_ACT_1970",
        "title": "The Patents Act, 1970 (Consolidated till 2024)",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "PATENT",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2024",
        "effective_from": "1972-04-20",
        "effective_to": None,
        "status": "CURRENT"
    },
    "biodiversity_act": {
        "document_id": "BIODIVERSITY_ACT_2002",
        "title": "The Biological Diversity Act, 2002",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "BIODIVERSITY_ABS",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2002",
        "effective_from": "2003-02-05",
        "effective_to": None,
        "status": "CURRENT"
    },
    "biodiversity_rules_2004": {
        "document_id": "BIODIVERSITY_RULES_2004",
        "title": "The Biological Diversity Rules, 2004",
        "document_type": "RULES",
        "jurisdiction": "INDIA",
        "domain": "BIODIVERSITY_ABS",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2004",
        "effective_from": "2004-04-15",
        "effective_to": None,
        "status": "CURRENT"
    },
    "nba_abs_guidelines": {
        "document_id": "NBA_ABS_GUIDELINES_2014",
        "title": "Guidelines on Access to Biological Resources and Associated Knowledge and Benefits Sharing Regulations, 2014",
        "document_type": "GUIDELINES",
        "jurisdiction": "INDIA",
        "domain": "BIODIVERSITY_ABS",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2014",
        "effective_from": "2014-11-21",
        "effective_to": None,
        "status": "CURRENT"
    },
    "drugs_cosmetics_act": {
        "document_id": "DRUGS_COSMETICS_ACT_1940",
        "title": "The Drugs and Cosmetics Act, 1940 and Rules, 1945 (Ayurvedic/Siddha/Unani Provisions)",
        "document_type": "STATUTE_REGULATION",
        "jurisdiction": "INDIA",
        "domain": "AYUSH_DRUG_REGULATION",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2016",
        "effective_from": "1940-04-10",
        "effective_to": None,
        "status": "CURRENT"
    },
    "fssai_ayurveda_aahar": {
        "document_id": "FSSAI_AYURVEDA_AAHARA_2022",
        "title": "Food Safety and Standards (Ayurveda Aahara) Regulations, 2022",
        "document_type": "REGULATION",
        "jurisdiction": "INDIA",
        "domain": "AYURVEDA_FOOD",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2022",
        "effective_from": "2022-05-05",
        "effective_to": None,
        "status": "CURRENT"
    },
    "trademarks_act": {
        "document_id": "TRADEMARKS_ACT_1999",
        "title": "The Trade Marks Act, 1999",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "TRADEMARK",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "1999",
        "effective_from": "2003-09-15",
        "effective_to": None,
        "status": "CURRENT"
    },
    "gi_act": {
        "document_id": "GI_ACT_1999",
        "title": "Geographical Indications of Goods (Registration and Protection) Act, 1999",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "GEOGRAPHICAL_INDICATION",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "1999",
        "effective_from": "2003-09-15",
        "effective_to": None,
        "status": "CURRENT"
    },
    "designs_act": {
        "document_id": "DESIGNS_ACT_2000",
        "title": "The Designs Act, 2000",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "DESIGN",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2000",
        "effective_from": "2001-05-11",
        "effective_to": None,
        "status": "CURRENT"
    },
    "ppvfr_act": {
        "document_id": "PPVFR_ACT_2001",
        "title": "Protection of Plant Varieties and Farmers Rights Act, 2001",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "PLANT_VARIETY",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2001",
        "effective_from": "2001-10-30",
        "effective_to": None,
        "status": "CURRENT"
    },
    "dmr_act": {
        "document_id": "DMR_ACT_1954",
        "title": "The Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954",
        "document_type": "STATUTE",
        "jurisdiction": "INDIA",
        "domain": "ADVERTISING_REGULATION",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "1954",
        "effective_from": "1955-04-01",
        "effective_to": None,
        "status": "CURRENT"
    },
    "cbd": {
        "document_id": "CBD_CONVENTION_1992",
        "title": "Convention on Biological Diversity (Rio Convention)",
        "document_type": "TREATY",
        "jurisdiction": "INTERNATIONAL",
        "domain": "BIODIVERSITY",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "1992",
        "effective_from": "1993-12-29",
        "effective_to": None,
        "status": "CURRENT"
    },
    "nagoya_protocol": {
        "document_id": "NAGOYA_PROTOCOL_2010",
        "title": "Nagoya Protocol on Access to Genetic Resources and Benefit Sharing",
        "document_type": "TREATY",
        "jurisdiction": "INTERNATIONAL",
        "domain": "ABS",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2010",
        "effective_from": "2014-10-12",
        "effective_to": None,
        "status": "CURRENT"
    },
    "trips": {
        "document_id": "TRIPS_AGREEMENT_1994",
        "title": "Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)",
        "document_type": "TREATY",
        "jurisdiction": "INTERNATIONAL",
        "domain": "IP_TREATY",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "1994",
        "effective_from": "1995-01-01",
        "effective_to": None,
        "status": "CURRENT"
    },
    "wipo_gratk": {
        "document_id": "WIPO_GRATK_TREATY_2024",
        "title": "WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge",
        "document_type": "TREATY",
        "jurisdiction": "INTERNATIONAL",
        "domain": "GENETIC_RESOURCES_TK",
        "authority_tier": "TIER_1_AUTHORITATIVE",
        "version": "2024",
        "effective_from": "2024-05-24",
        "effective_to": None,
        "status": "CURRENT"
    }
}


def extract_legal_hierarchy(text: str, category: str) -> Dict[str, Optional[str]]:
    """Extracts explicit section, rule, or article references from statutory chunk text."""
    meta: Dict[str, Optional[str]] = {"section": None, "rule": None, "article": None}

    # 1. Category-specific targeted legal references
    if category == "patents_act":
        if re.search(r"\(p\)\s+an\s+invention\s+which[,\s]+in\s+effect[,\s]+is\s+traditional\s+knowledge", text, re.I):
            meta["section"] = "3(p)"
            return meta
        if re.search(r"\(e\)\s+a\s+substance\s+obtained\s+by\s+a\s+mere\s+admixture", text, re.I):
            meta["section"] = "3(e)"
            return meta
        if re.search(r"\(d\)\s+the\s+mere\s+discovery\s+of\s+a\s+new\s+form", text, re.I):
            meta["section"] = "3(d)"
            return meta
        if re.search(r"\(j\)\s+plants\s+and\s+animals\s+in\s+whole", text, re.I):
            meta["section"] = "3(j)"
            return meta
        if re.search(r"\(k\)\s+a\s+mathematical\s+or\s+business\s+method", text, re.I):
            meta["section"] = "3(k)"
            return meta

    if category == "biodiversity_act":
        if re.search(r"Application\s+for\s+intellectual\s+property\s+rights|6\.\s*\(\d+\)\s*No\s+person\s+shall\s+apply\s+for\s+any\s+intellectual\s+property", text, re.I):
            meta["section"] = "6"
            return meta
        if re.search(r"55\.\s*\(\d+\)\s*Whoever\s+contravenes", text, re.I):
            meta["section"] = "55"
            return meta
        if re.search(r"40\.\s*Notwithstanding\s+anything\s+contained|normally\s+traded\s+as\s+commodities", text, re.I):
            meta["section"] = "40"
            return meta
        if re.search(r"19\.\s*\(\d+\)\s*Any\s+person\s+referred|Approval\s+by\s+National\s+Biodiversity\s+Authority", text, re.I):
            meta["section"] = "19"
            return meta

    # 2. General pattern matching for Statutes, Rules, and Treaties
    # Section pattern: "Section 3", "3.", etc.
    sec_match = re.search(r"(?:^|\n)\s*(\d+[A-Za-z]?)\.\s+([A-Z][^\n]+)", text)
    if sec_match and not meta["section"]:
        meta["section"] = sec_match.group(1).strip()

    # Rule pattern
    if "rule" in category or "guidelines" in category or "aahar" in category:
        rule_match = re.search(r"(?:^|\n)\s*(?:Rule\s+|Regulation\s+)?(\d+[A-Za-z]?)\.\s+([A-Z][^\n]+)", text, re.I)
        if rule_match:
            meta["rule"] = rule_match.group(1).strip()

    # Article pattern for treaties
    art_match = re.search(r"(?:^|\n)\s*Article\s+(\d+[A-Za-z]?)", text, re.I)
    if art_match:
        meta["article"] = art_match.group(1).strip()

    return meta


def load_manifest(manifest_path: Path) -> Dict[str, Dict[str, Any]]:
    """Loads authoritative manifest."""
    manifest = {}
    if not manifest_path.exists():
        return manifest
    with open(manifest_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row.get("category", "").strip()
            if cat:
                manifest[cat] = row
    return manifest


def ingest_legal_knowledge_base(
    jsonl_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None
) -> List[LegalEvidenceChunk]:
    """
    Ingests and parses all RAG 2 legal evidence chunks, extracting legal structure,
    attaching version and temporal metadata, and deduplicating by content hash.
    """
    target_jsonl = jsonl_path or settings.RAG2_DATA_JSONL_PATH
    target_csv = csv_path or settings.RAG2_DATA_CSV_PATH
    target_manifest = manifest_path or settings.RAG2_MANIFEST_PATH

    manifest = load_manifest(target_manifest)
    chunks: List[LegalEvidenceChunk] = []
    seen_hashes = set()

    if target_jsonl and target_jsonl.exists():
        logger.info(f"Ingesting RAG 2 legal records from JSONL: {target_jsonl}")
        with open(target_jsonl, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except Exception as e:
                    logger.warning(f"Skipping malformed JSON line {line_idx}: {e}")
                    continue

                ch = _build_legal_chunk(raw, manifest)
                if ch:
                    if ch.content_hash and ch.content_hash in seen_hashes:
                        continue
                    if ch.content_hash:
                        seen_hashes.add(ch.content_hash)
                    chunks.append(ch)

    elif target_csv and target_csv.exists():
        logger.info(f"JSONL not found. Falling back to CSV: {target_csv}")
        with open(target_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                ch = _build_legal_chunk(raw, manifest)
                if ch:
                    if ch.content_hash and ch.content_hash in seen_hashes:
                        continue
                    if ch.content_hash:
                        seen_hashes.add(ch.content_hash)
                    chunks.append(ch)
    else:
        logger.error(f"No RAG 2 data source files found at {target_jsonl} or {target_csv}")

    logger.info(f"Successfully ingested {len(chunks)} authoritative legal & regulatory chunks.")
    return chunks


def _build_legal_chunk(raw: Dict[str, Any], manifest: Dict[str, Dict[str, Any]]) -> Optional[LegalEvidenceChunk]:
    """Constructs and enriches a single LegalEvidenceChunk."""
    record_id = raw.get("record_id") or f"RAG2-{raw.get('chunk_index', 0):05d}"
    text = (raw.get("text") or "").strip()
    if not text:
        return None

    category = (raw.get("category") or "general_statute").strip().lower()
    doc_meta = DOCUMENT_METADATA_MAP.get(category, {})

    # Hierarchy extraction
    hierarchy = extract_legal_hierarchy(text, category)

    document_id = doc_meta.get("document_id", category.upper())
    title = doc_meta.get("title", raw.get("document_title") or "Authoritative Legal Document")
    domain = raw.get("domain") or doc_meta.get("domain", "STATUTORY_LAW")
    doc_type = raw.get("document_type") or doc_meta.get("document_type", "STATUTE")
    jurisdiction = raw.get("jurisdiction") or doc_meta.get("jurisdiction", "INDIA")
    authority_tier = doc_meta.get("authority_tier", "TIER_1_AUTHORITATIVE")
    source_url = raw.get("source_url") or (manifest.get(category, {}).get("source_url") if manifest else None)

    return LegalEvidenceChunk(
        record_id=record_id,
        chunk_id=record_id,
        document_id=document_id,
        category=category,
        domain=domain,
        document_type=doc_type,
        document_title=title,
        source_url=source_url,
        jurisdiction=jurisdiction,
        authority_tier=authority_tier,
        rag_role="legal_regulatory_evidence",
        section=hierarchy.get("section"),
        rule=hierarchy.get("rule"),
        article=hierarchy.get("article"),
        version=doc_meta.get("version", "2026"),
        effective_from=doc_meta.get("effective_from", "2000-01-01"),
        effective_to=doc_meta.get("effective_to"),
        status=doc_meta.get("status", "CURRENT"),
        language="en",
        chunk_index=int(raw.get("chunk_index", 0)),
        text=text,
        content_hash=raw.get("content_hash"),
        source_corpus=raw.get("source_corpus", "rag2_legal_regulatory_evidence.jsonl")
    )
