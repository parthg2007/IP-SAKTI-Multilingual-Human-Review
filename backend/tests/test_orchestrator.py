"""Unit and integration tests for Connectable Multi-RAG Orchestrator."""
import unittest
import asyncio
from app.rag1.service import rag1_service
from app.orchestrator.registry import rag_registry
from app.orchestrator.local_connector import LocalRAG1Connector
from app.orchestrator.mock_rag2_connector import MockRAG2Connector
from app.orchestrator.http_connector import HTTPRAGConnector
from app.orchestrator.router import query_router
from app.orchestrator.service import orchestrator_service
from app.data.models import MultiRAGQueryRequest


class TestMultiRAGOrchestrator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Initialize RAG 1 and register connectors
        if not rag1_service.is_ready:
            rag1_service.initialize()
        rag_registry.register(LocalRAG1Connector())
        rag_registry.register(MockRAG2Connector())

    def test_query_router_decisions(self):
        # 1. Pure conceptual query -> RAG 1
        d1 = query_router.route("What is a classical Ayurvedic formulation?")
        self.assertIn("rag1_domain_knowledge", d1.target_rags)
        self.assertEqual(d1.primary_rag, "rag1_domain_knowledge")
        self.assertEqual(d1.intent, "conceptual_domain_knowledge")

        # 2. Hybrid query -> Both RAG 1 and RAG 2
        d2 = query_router.route("How can an Ayurvedic product be protected using IP?")
        self.assertIn("rag1_domain_knowledge", d2.target_rags)
        self.assertIn("rag2_legal_regulatory", d2.target_rags)
        self.assertEqual(d2.intent, "hybrid_domain_and_legal")

        # 3. Legal penalty query -> RAG 2
        d3 = query_router.route("What is the penalty and criminal liability under Section 55?")
        self.assertIn("rag2_legal_regulatory", d3.target_rags)
        self.assertEqual(d3.intent, "authoritative_legal_statute")

    async def test_multi_rag_query_execution(self):
        req = MultiRAGQueryRequest(
            query="How can an Ayurvedic formulation be protected under Indian Patent Law?",
            top_k_per_rag=3
        )
        res = await orchestrator_service.execute_query(req)

        self.assertIsNotNone(res.domain_context)
        self.assertIsNotNone(res.legal_evidence_context)
        self.assertIn("rag1_domain_knowledge", res.connected_rags_responded)
        self.assertIn("rag2_legal_regulatory", res.connected_rags_responded)
        self.assertGreater(len(res.citations), 0)

        # Verify citation authority tier separation
        tiers = set(c.authority_tier for c in res.citations)
        self.assertTrue("statutory_authority" in tiers or "auxiliary_seed" in tiers)

    async def test_dynamic_rag_registration(self):
        # Test connecting a third external RAG service (e.g. Clinical Trials / Prior Art RAG)
        ext_rag = HTTPRAGConnector(
            rag_id="rag3_clinical_trials",
            endpoint_url="http://localhost:9000",
            name="RAG 3: Clinical Trials Knowledge",
            role="clinical_evidence"
        )
        rag_registry.register(ext_rag)

        registered = rag_registry.get("rag3_clinical_trials")
        self.assertIsNotNone(registered)
        self.assertEqual(registered.role, "clinical_evidence")

        # Check in status list
        statuses = await rag_registry.get_status_list()
        rag_ids = [s.rag_id for s in statuses]
        self.assertIn("rag3_clinical_trials", rag_ids)

        # Clean up
        rag_registry.unregister("rag3_clinical_trials")
        self.assertIsNone(rag_registry.get("rag3_clinical_trials"))


if __name__ == "__main__":
    unittest.main()
