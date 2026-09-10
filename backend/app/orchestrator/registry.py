"""RAG Registry for managing and discovering connected RAG services."""
import logging
from typing import Dict, List, Optional
from app.orchestrator.base_connector import BaseRAGConnector
from app.data.models import RAGInfo

logger = logging.getLogger(__name__)


class RAGRegistry:
    """
    Central registry for connected RAG instances in IP-SAKTI.
    Allows modular attachment of domain RAGs, legal RAGs, and external microservices.
    """

    def __init__(self):
        self._connectors: Dict[str, BaseRAGConnector] = {}

    def register(self, connector: BaseRAGConnector) -> None:
        """Registers a new RAG connector."""
        self._connectors[connector.rag_id] = connector
        logger.info(f"Registered RAG connector '{connector.rag_id}' ({connector.name})")

    def unregister(self, rag_id: str) -> Optional[BaseRAGConnector]:
        """Removes a RAG connector."""
        if rag_id in self._connectors:
            removed = self._connectors.pop(rag_id)
            logger.info(f"Unregistered RAG connector '{rag_id}'")
            return removed
        return None

    def get(self, rag_id: str) -> Optional[BaseRAGConnector]:
        """Retrieves a RAG connector by ID."""
        return self._connectors.get(rag_id)

    def list_all(self) -> List[BaseRAGConnector]:
        """Returns all registered connectors."""
        return list(self._connectors.values())

    async def get_status_list(self) -> List[RAGInfo]:
        """Returns health and capability details for all registered RAGs."""
        info_list: List[RAGInfo] = []
        for connector in self._connectors.values():
            is_healthy = await connector.health_check()
            endpoint_url = getattr(connector, "endpoint_url", None)
            info_list.append(
                RAGInfo(
                    rag_id=connector.rag_id,
                    name=connector.name,
                    role=connector.role,
                    connector_type=connector.connector_type,
                    is_healthy=is_healthy,
                    authority_tier=connector.authority_tier,
                    description=connector.description,
                    endpoint_url=endpoint_url
                )
            )
        return info_list


# Global registry singleton
rag_registry = RAGRegistry()
