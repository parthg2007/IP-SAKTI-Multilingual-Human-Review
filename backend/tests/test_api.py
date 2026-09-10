"""Integration test for FastAPI REST API endpoints."""
import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("service", data)
        self.assertIn("endpoints", data)

    def test_rag1_health_endpoint(self):
        res = self.client.get("/api/v1/rag/knowledge/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["total_chunks"], 0)

    def test_rag1_query_endpoint(self):
        payload = {
            "query": "What is TKDL and how many volumes of Ayurveda are transcribed?",
            "top_k": 3
        }
        res = self.client.post("/api/v1/rag/knowledge/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["query"], payload["query"])
        self.assertGreater(len(data["evidence"]), 0)
        self.assertIn("RAG 1", data["answer_context"])

    def test_rag1_search_endpoint(self):
        payload = {
            "query": "Traditional Knowledge Patent Bar Section 3(p)",
            "mode": "hybrid",
            "top_k": 3
        }
        res = self.client.post("/api/v1/rag/knowledge/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mode"], "hybrid")
        self.assertGreater(data["total_hits"], 0)

    def test_orchestrator_route_endpoint(self):
        res = self.client.post("/api/v1/orchestrator/route?query=How can an Ayurvedic product be protected using IP?")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("rag1_domain_knowledge", data["target_rags"])
        self.assertIn("rag2_legal_regulatory", data["target_rags"])

    def test_orchestrator_query_endpoint(self):
        payload = {
            "query": "Can an Ayurvedic formulation get patent protection in India?",
            "top_k_per_rag": 2
        }
        res = self.client.post("/api/v1/orchestrator/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("synthesized_answer", data)
        self.assertGreater(len(data["citations"]), 0)

    def test_rag2_health_endpoint(self):
        res = self.client.get("/api/v1/rag/legal/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["total_chunks"], 2000)

    def test_rag2_query_endpoint(self):
        payload = {
            "query": "Is prior approval from NBA required under Section 6 for patent applications?",
            "top_k": 3
        }
        res = self.client.post("/api/v1/rag/legal/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data["citations"]), 0)
        self.assertIn("Section 6", data["answer_context"])

    def test_rag2_search_endpoint(self):
        payload = {
            "query": "Section 3(p) traditional knowledge",
            "mode": "hybrid",
            "top_k": 3
        }
        res = self.client.post("/api/v1/rag/legal/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_hits"], 0)

    def test_rag2_historical_endpoint(self):
        payload = {
            "query": "Biological Diversity Act",
            "requested_date": "2015-01-01"
        }
        res = self.client.post("/api/v1/rag/legal/historical", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_current_law"])

    def test_rag2_documents_endpoint(self):
        res = self.client.get("/api/v1/rag/legal/documents/patents_act")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["category"], "patents_act")
        self.assertGreater(data["total_chunks"], 0)


if __name__ == "__main__":
    unittest.main()
