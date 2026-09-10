"""FastAPI routes for Multi-RAG Orchestrator and dynamic RAG connectivity."""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.data.models import (
    MultiRAGQueryRequest,
    MultiRAGQueryResponse,
    RAGRouteDecision,
    RAGRegistrationRequest,
    RAGInfo
)
from app.orchestrator.service import orchestrator_service, KnowledgeServiceUnavailable
from app.orchestrator.router import query_router
from app.orchestrator.registry import rag_registry
from app.orchestrator.http_connector import HTTPRAGConnector

router = APIRouter(prefix="/api/v1/orchestrator", tags=["Multi-RAG Orchestrator"])


@router.post(
    "/query",
    response_model=MultiRAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Federated Multi-RAG Query",
    description="Routes and executes query across RAG 1 (Domain Knowledge), RAG 2 (Legal Evidence), and other connected RAGs."
)
async def query_multi_rag(request: MultiRAGQueryRequest):
    try:
        return await orchestrator_service.execute_query(request)
    except KnowledgeServiceUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-RAG orchestration failed: {str(e)}"
        )


@router.post(
    "/route",
    response_model=RAGRouteDecision,
    status_code=status.HTTP_200_OK,
    summary="Analyze Query Intent and Routing",
    description="Returns which RAG units should handle the query and the reason."
)
async def route_query(query: str):
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")
    return query_router.route(query.strip())


@router.get(
    "/rags",
    response_model=List[RAGInfo],
    status_code=status.HTTP_200_OK,
    summary="List Registered RAG Architectures",
    description="Returns connectivity status, role, and health of all connected RAG units."
)
async def list_registered_rags():
    return await rag_registry.get_status_list()


@router.post(
    "/rags/register",
    status_code=status.HTTP_201_CREATED,
    summary="Dynamically Connect an External RAG Service",
    description="Registers an external HTTP RAG microservice (such as RAG 2 or clinical trial RAG) at runtime."
)
async def register_external_rag(request: RAGRegistrationRequest):
    existing = rag_registry.get(request.rag_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"RAG with id '{request.rag_id}' is already registered."
        )

    connector = HTTPRAGConnector(
        rag_id=request.rag_id,
        endpoint_url=request.endpoint_url,
        name=request.name,
        role=request.role,
        authority_tier=request.authority_tier or "statutory_authority",
        description=request.description
    )

    rag_registry.register(connector)
    return {
        "message": f"External RAG '{request.rag_id}' successfully connected to IP-SAKTI orchestrator.",
        "rag_id": request.rag_id,
        "endpoint_url": request.endpoint_url
    }
