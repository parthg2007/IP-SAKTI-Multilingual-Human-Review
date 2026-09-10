"""Abstract Base Connector for connectable RAG architectures."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from app.data.models import RAGEvidence


class BaseRAGConnector(ABC):
    """
    Standard interface for all connected RAG units in IP-SAKTI.
    Allows RAG 1 to connect with RAG 2 (Legal & Regulatory Evidence)
    and any future specialized RAG instances.
    """

    def __init__(
        self,
        rag_id: str,
        name: str,
        role: str,
        authority_tier: str,
        description: str,
        connector_type: str = "custom"
    ):
        self.rag_id = rag_id
        self.name = name
        self.role = role
        self.authority_tier = authority_tier
        self.description = description
        self.connector_type = connector_type

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[RAGEvidence]:
        """Retrieves raw evidence snippets from this RAG unit."""
        pass

    @abstractmethod
    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[RAGEvidence], float]:
        """
        Executes query on this RAG unit.
        Returns (answer_context, evidence_list, retrieval_score).
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Returns True if the underlying RAG system is available."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Returns metadata about this RAG connector."""
        return {
            "rag_id": self.rag_id,
            "name": self.name,
            "role": self.role,
            "authority_tier": self.authority_tier,
            "connector_type": self.connector_type,
            "description": self.description
        }
