"""In-process local connector for RAG 1 Domain Knowledge."""
from typing import List, Dict, Any, Tuple, Optional
from app.orchestrator.base_connector import BaseRAGConnector
from app.data.models import RAGEvidence, RAGQueryRequest
from app.rag1.service import rag1_service


class LocalRAG1Connector(BaseRAGConnector):
    """
    Connects the Multi-RAG Orchestrator to RAG 1 in-process.
    Provides Ayurveda and Intellectual Property conceptual knowledge.
    """

    def __init__(self):
        super().__init__(
            rag_id="rag1_domain_knowledge",
            name="RAG 1: Ayurveda + IP Domain Knowledge",
            role="domain_context",
            authority_tier="auxiliary_seed",
            description="Domain knowledge layer for Ayurveda, medicinal plants, formulations, and IP terminology.",
            connector_type="in_process"
        )

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[RAGEvidence]:
        domain = filters.get("domain") if filters else None
        req = RAGQueryRequest(query=query, domain=domain, top_k=top_k,
                              jurisdiction=(filters or {}).get("jurisdiction"), language=(filters or {}).get("language"))
        response = rag1_service.query(req)
        return response.evidence

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[RAGEvidence], float]:
        domain = filters.get("domain") if filters else None
        top_k = filters.get("top_k", 5) if filters else 5
        req = RAGQueryRequest(query=query, domain=domain, top_k=top_k,
                              jurisdiction=(filters or {}).get("jurisdiction"), language=(filters or {}).get("language"))
        response = rag1_service.query(req)
        return response.answer_context, response.evidence, response.retrieval_score

    async def health_check(self) -> bool:
        return rag1_service.is_ready
