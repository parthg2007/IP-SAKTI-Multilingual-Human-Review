"""FastAPI router for RAG 2 (Legal & Regulatory Evidence)."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.rag2.models import (
    LegalQueryRequest,
    LegalQueryResponse,
    HistoricalQueryRequest,
    HistoricalQueryResponse,
    LegalSearchRequest,
    LegalSearchResponse,
    RAG2HealthResponse
)
from app.rag2.service import rag2_service

router = APIRouter(prefix="/api/v1/rag/legal", tags=["RAG 2: Legal & Regulatory Evidence"])


@router.post("/query", response_model=LegalQueryResponse, summary="Query authoritative legal and regulatory evidence")
async def legal_query(request: LegalQueryRequest):
    """Answers legal and regulatory queries with authoritative statutory citations and section provenance."""
    try:
        return rag2_service.query(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical", response_model=HistoricalQueryResponse, summary="Query historical point-in-time legal validity")
async def historical_query(request: HistoricalQueryRequest):
    """Evaluates whether legal provisions were active and in force as of a requested historical date."""
    try:
        return rag2_service.historical_query(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=LegalSearchResponse, summary="Search statutory and regulatory chunks")
async def legal_search(request: LegalSearchRequest):
    """Granular statutory search supporting hybrid, bm25, or dense vector retrieval."""
    try:
        return rag2_service.search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", summary="Get statutory document metadata and sample chunks")
async def get_document(document_id: str):
    """Retrieves document overview, jurisdiction, authority tier, and chunk counts."""
    res = rag2_service.get_document(document_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/health", response_model=RAG2HealthResponse, summary="RAG 2 operational health check")
async def legal_health():
    """Returns total indexed statutory chunks, categories, and retrieval engine status."""
    return rag2_service.health()
