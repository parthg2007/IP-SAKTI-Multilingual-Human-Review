"""Pydantic schemas and data contracts for RAG 2 (Legal & Regulatory Evidence)."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
from app.data.models import RAGEvidence


class LegalEvidenceChunk(BaseModel):
    """Authoritative legal evidence chunk with full statutory provenance."""
    record_id: str = Field(..., description="Unique record identifier (e.g. RAG2-00001)")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Statutory document ID (e.g. PATENTS_ACT, BIODIVERSITY_ACT)")
    category: str = Field(..., description="Source legal category (e.g. patents_act, biodiversity_act)")
    domain: str = Field(..., description="Legal domain (e.g. PATENT, BIODIVERSITY_ABS, AYUSH_DRUG_REGULATION)")
    document_type: str = Field("STATUTE", description="STATUTE, RULES, REGULATION, TREATY, or GUIDELINES")
    document_title: str = Field(..., description="Official title of the enactment or source document")
    source_url: Optional[str] = Field(None, description="Authoritative primary source URL")
    jurisdiction: str = Field("INDIA", description="Applicable legal jurisdiction (e.g. INDIA, INTERNATIONAL)")
    authority_tier: str = Field("TIER_1_AUTHORITATIVE", description="TIER_1_AUTHORITATIVE, TIER_2_SUPPORTING, etc.")
    rag_role: str = Field("legal_regulatory_evidence", description="RAG architecture role")
    section: Optional[str] = Field(None, description="Extracted statutory section (e.g. 3(p), 3(e), 6, 40)")
    rule: Optional[str] = Field(None, description="Extracted administrative rule number (e.g. 161, 14)")
    article: Optional[str] = Field(None, description="Extracted treaty article number (e.g. 27, 8(j))")
    version: str = Field("2026", description="Consolidated enactment version")
    effective_from: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    effective_to: Optional[str] = Field(None, description="Date superseded or repealed (YYYY-MM-DD), or null if active")
    status: str = Field("CURRENT", description="CURRENT, REPEALED, or AMENDED")
    language: str = Field("en", description="Language code")
    chunk_index: int = Field(0, description="Sequential chunk index in parent document")
    text: str = Field(..., description="Statutory or regulatory text body")
    content_hash: Optional[str] = Field(None, description="SHA256 content hash")
    source_corpus: Optional[str] = Field(None, description="Source provenance file")


class LegalCitation(BaseModel):
    """Exact citation ensuring full provenance chain."""
    document_id: str
    title: str
    section: Optional[str] = None
    rule: Optional[str] = None
    article: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    version: Optional[str] = None
    chunk_id: str
    effective_from: Optional[str] = None
    authority_tier: str
    relevance_score: Optional[float] = None
    jurisdiction: Optional[str] = "INDIA"


class LegalQueryRequest(BaseModel):
    """Request payload for POST /api/v1/rag/legal/query."""
    query: str = Field(..., description="Legal or regulatory query string", min_length=1)
    jurisdiction: Optional[str] = Field("INDIA", description="Legal jurisdiction (INDIA or INTERNATIONAL)")
    domains: Optional[List[str]] = Field(None, description="Target legal domains filter")
    categories: Optional[List[str]] = Field(None, description="Specific document category filters")
    language: Optional[str] = Field(None, description="Language hint (en, hi, hi-Latn)")
    top_k: Optional[int] = Field(5, description="Number of evidence chunks to retrieve", ge=1, le=20)
    as_of_date: Optional[str] = Field(None, description="Point-in-time date for historical validity (YYYY-MM-DD)")

    @field_validator("as_of_date")
    @classmethod
    def validate_date(cls, value):
        if value is not None:
            return date.fromisoformat(value).isoformat()
        return value


class LegalQueryResponse(BaseModel):
    """Response payload for POST /api/v1/rag/legal/query."""
    query: str
    jurisdiction: str
    language: str
    answer_context: str
    evidence: List[RAGEvidence]
    citations: List[LegalCitation]
    retrieval_metadata: Dict[str, Any]
    conflict_detected: bool = False
    conflict_details: Optional[str] = None
    disclaimer: str = (
        "RAG 2 provides authoritative statutory provisions and regulatory citations. "
        "It does not constitute formal legal counsel. Official submissions require validation by a qualified patent agent or advocate."
    )


class HistoricalQueryRequest(BaseModel):
    """Request payload for POST /api/v1/rag/legal/historical."""
    query: str = Field(..., description="Query about historical legal standing", min_length=1)
    requested_date: str = Field(..., description="Target historical date (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Specific enactment category (e.g. patents_act)")
    top_k: Optional[int] = Field(5, description="Number of provisions to retrieve", ge=1, le=20)

    @field_validator("requested_date")
    @classmethod
    def validate_date(cls, value):
        return date.fromisoformat(value).isoformat()


class HistoricalQueryResponse(BaseModel):
    """Response payload for POST /api/v1/rag/legal/historical."""
    query: str
    requested_date: str
    is_current_law: bool
    applicable_provisions: List[LegalCitation]
    evidence: List[RAGEvidence]
    explanation: str


class LegalSearchRequest(BaseModel):
    """Request payload for POST /api/v1/rag/legal/search."""
    query: str = Field(..., description="Search terms, section names, or numbers", min_length=1)
    mode: Optional[str] = Field("hybrid", description="Search mode: hybrid, bm25, or vector")
    category: Optional[str] = Field(None, description="Category filter (e.g. patents_act, biodiversity_act)")
    domain: Optional[str] = Field(None, description="Domain filter (e.g. PATENT, BIODIVERSITY_ABS)")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction filter")
    top_k: Optional[int] = Field(10, description="Max results to return", ge=1, le=50)


class LegalSearchHit(BaseModel):
    """Individual legal search hit item."""
    chunk_id: str
    document_id: str
    title: str
    category: str
    domain: str
    section: Optional[str] = None
    rule: Optional[str] = None
    article: Optional[str] = None
    text: str
    source_url: Optional[str] = None
    authority_tier: str
    score: float
    retrieval_method: str


class LegalSearchResponse(BaseModel):
    """Response payload for POST /api/v1/rag/legal/search."""
    query: str
    mode: str
    total_hits: int
    results: List[LegalSearchHit]


class RAG2HealthResponse(BaseModel):
    """Operational health response for RAG 2."""
    status: str
    rag_id: str = "RAG2_LEGAL_REGULATORY"
    total_chunks: int
    categories_indexed: List[str]
    domains_indexed: List[str]
    retrievers_active: List[str]
