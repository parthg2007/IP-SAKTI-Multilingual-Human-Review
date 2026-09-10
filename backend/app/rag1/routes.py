"""FastAPI routes for RAG 1 Domain Knowledge service."""
from fastapi import APIRouter, HTTPException, status
from app.data.models import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGHealthResponse
)
from app.rag1.service import rag1_service

router = APIRouter(prefix="/api/v1/rag/knowledge", tags=["RAG 1 - Domain Knowledge"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Ayurveda & IP Domain Knowledge",
    description="Answers domain concept questions with structured evidence context and source attribution."
)
async def query_knowledge(request: RAGQueryRequest):
    try:
        return rag1_service.query(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process knowledge query: {str(e)}"
        )


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Knowledge Base Chunks",
    description="Granular search across domain chunks with support for hybrid, vector, and bm25 search."
)
async def search_knowledge(request: RAGSearchRequest):
    try:
        return rag1_service.search(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute knowledge search: {str(e)}"
        )


@router.get(
    "/health",
    response_model=RAGHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG 1 Health & Index Status",
    description="Checks operational status and returns index metrics for RAG 1."
)
async def check_health():
    return rag1_service.health()
