"""In-process local connector for RAG 2 (Authoritative Legal & Regulatory Evidence)."""
from typing import List, Dict, Any, Tuple, Optional
from app.orchestrator.base_connector import BaseRAGConnector
from app.data.models import RAGEvidence
from app.rag2.models import LegalQueryRequest
from app.rag2.service import rag2_service


class LocalRAG2Connector(BaseRAGConnector):
    """
    Connects the Multi-RAG Orchestrator to the production RAG 2 Legal & Regulatory service in-process.
    Provides authoritative statutory evidence across Patents Act, Biological Diversity Act,
    D&C Act AYUSH rules, FSSAI Ayurveda Aahara, and international treaties.
    """

    def __init__(self):
        super().__init__(
            rag_id="rag2_legal_regulatory",
            name="RAG 2: Legal & Regulatory Evidence (Authoritative)",
            role="authoritative_legal",
            authority_tier="statutory_authority",
            description="Authoritative legal repository covering Indian IP laws, BD Act, AYUSH regulations, and treaties.",
            connector_type="in_process"
        )

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[RAGEvidence]:
        categories = [filters["category"]] if filters and "category" in filters else None
        domains = [filters["domain"]] if filters and "domain" in filters else None
        jurisdiction = filters.get("jurisdiction", "INDIA") if filters else "INDIA"

        req = LegalQueryRequest(
            query=query,
            categories=categories,
            domains=domains,
            jurisdiction=jurisdiction,
            language=(filters or {}).get("language"),
            top_k=top_k
        )
        res = rag2_service.query(req)
        return res.evidence

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[RAGEvidence], float]:
        top_k = filters.get("top_k", 5) if filters else 5
        categories = [filters["category"]] if filters and "category" in filters else None
        domains = [filters["domain"]] if filters and "domain" in filters else None
        jurisdiction = filters.get("jurisdiction", "INDIA") if filters else "INDIA"

        req = LegalQueryRequest(
            query=query,
            categories=categories,
            domains=domains,
            jurisdiction=jurisdiction,
            language=(filters or {}).get("language"),
            top_k=top_k
        )
        res = rag2_service.query(req)
        top_score = res.evidence[0].score if res.evidence else 0.0
        return res.answer_context, res.evidence, top_score

    async def health_check(self) -> bool:
        return rag2_service.is_ready
