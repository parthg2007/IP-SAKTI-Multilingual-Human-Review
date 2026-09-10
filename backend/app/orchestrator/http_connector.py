"""HTTP REST Connector for remote RAG architectures (e.g. RAG 2)."""
import logging
from typing import List, Dict, Any, Tuple, Optional
import httpx

from app.orchestrator.base_connector import BaseRAGConnector
from app.data.models import RAGEvidence
from app.config import settings

logger = logging.getLogger(__name__)


class HTTPRAGConnector(BaseRAGConnector):
    """
    Connects to an external RAG service over HTTP/REST.
    Used for connecting RAG 2 (Legal & Regulatory Evidence) or other distributed RAGs.
    """

    def __init__(
        self,
        rag_id: str,
        endpoint_url: str,
        name: Optional[str] = None,
        role: str = "authoritative_legal",
        authority_tier: str = "statutory_authority",
        description: Optional[str] = None,
        timeout: float = None
    ):
        super().__init__(
            rag_id=rag_id,
            name=name or f"Remote RAG ({rag_id})",
            role=role,
            authority_tier=authority_tier,
            description=description or f"External RAG service hosted at {endpoint_url}",
            connector_type="http_rest"
        )
        self.endpoint_url = endpoint_url.rstrip("/")
        self.timeout = timeout or settings.RAG_TIMEOUT_SECONDS

    async def health_check(self) -> bool:
        """Pings the remote RAG's health check endpoint."""
        health_url = f"{self.endpoint_url}/api/v1/rag/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(health_url)
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for remote RAG {self.rag_id} at {health_url}: {e}")
            return False

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[RAGEvidence]:
        """Calls remote search/retrieval endpoint."""
        search_url = f"{self.endpoint_url}/api/v1/rag/search"
        payload = {
            "query": query,
            "top_k": top_k,
            **(filters or {})
        }
        evidence_list: List[RAGEvidence] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(search_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results") or data.get("evidence") or []
                    for idx, item in enumerate(results):
                        evidence_list.append(
                            RAGEvidence(
                                document_id=item.get("document_id", f"REMOTE-{idx}"),
                                chunk_id=item.get("chunk_id", f"REMOTE-CHK-{idx}"),
                                title=item.get("title", "Remote Legal Evidence"),
                                source_name=item.get("source_name", self.name),
                                source_url=item.get("source_url"),
                                text=item.get("text") or item.get("snippet"),
                                domain=item.get("domain", self.role),
                                score=item.get("score", 0.8),
                                authority_tier=self.authority_tier,
                                rag_source=self.rag_id
                            )
                        )
        except Exception as e:
            logger.error(f"Failed to retrieve from remote RAG {self.rag_id}: {e}")

        return evidence_list

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[RAGEvidence], float]:
        """Calls remote query endpoint."""
        query_url = f"{self.endpoint_url}/api/v1/rag/query"
        payload = {
            "query": query,
            **(filters or {})
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(query_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer_context = data.get("answer_context") or data.get("answer") or ""
                    retrieval_score = float(data.get("retrieval_score") or 0.85)
                    raw_evidence = data.get("evidence") or []
                    evidence_list: List[RAGEvidence] = []
                    for idx, ev in enumerate(raw_evidence):
                        evidence_list.append(
                            RAGEvidence(
                                document_id=ev.get("document_id", f"REMOTE-{idx}"),
                                chunk_id=ev.get("chunk_id", f"REMOTE-CHK-{idx}"),
                                title=ev.get("title", "Remote Legal Evidence"),
                                source_name=ev.get("source_name", self.name),
                                source_url=ev.get("source_url"),
                                text=ev.get("text"),
                                domain=ev.get("domain", self.role),
                                score=ev.get("score", retrieval_score),
                                authority_tier=self.authority_tier,
                                rag_source=self.rag_id
                            )
                        )
                    return answer_context, evidence_list, retrieval_score
        except Exception as e:
            logger.error(f"Remote RAG {self.rag_id} query call failed: {e}")

        raise RuntimeError(f"Remote RAG {self.rag_id} could not complete the query.")
