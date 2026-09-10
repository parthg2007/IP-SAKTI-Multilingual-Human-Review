"""Integration coverage for requests made by the React chat client."""
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.llm import groq_llm, SYSTEM_PROMPT
from app.orchestrator.registry import rag_registry
from app.rag2.service import rag2_service


class TestFrontendContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.llm_patch = patch.object(groq_llm, "_enabled", False)
        cls.llm_patch.start()
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        cls.llm_patch.stop()

    def query(self, **overrides):
        return self.client.post("/api/v1/orchestrator/query", json={
            "query": "Can an Ayurvedic formulation get patent protection?",
            "jurisdiction": "INDIA", "top_k_per_rag": 4, **overrides,
        })

    def test_frontend_payload_returns_answer_and_clickable_citations(self):
        response = self.query()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jurisdiction"], "INDIA")
        self.assertTrue(data["synthesized_answer"].strip())
        self.assertEqual(len(data["connected_rags_responded"]), 2)
        self.assertTrue(any(c["source_url"] for c in data["citations"]))
        self.assertLessEqual(len(data["citations"]), 8)

    def test_international_questions_only_retrieve_international_sources(self):
        for query in ["What is TRIPS?", "What is benefit sharing under the Nagoya Protocol?", "How is traditional knowledge protected?"]:
            with self.subTest(query=query):
                response = self.query(query=query, jurisdiction="INTERNATIONAL")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["jurisdiction"], "INTERNATIONAL")
                self.assertEqual(data["connected_rags_responded"], ["rag2_legal_regulatory"])
                self.assertTrue(data["citations"])
                chunks = {chunk.chunk_id: chunk for chunk in rag2_service.chunks}
                self.assertTrue(all(chunks[c["chunk_id"]].jurisdiction == "INTERNATIONAL" for c in data["citations"]))
                self.assertNotIn("Legal Assessment Summary", data["synthesized_answer"])
                self.assertNotIn("Statutory Qualification", data["synthesized_answer"])

    def test_blank_oversize_and_invalid_jurisdiction_are_rejected(self):
        for overrides in [{"query": "   "}, {"query": "a" * 4001}, {"jurisdiction": "MARS"}]:
            self.assertEqual(self.query(**overrides).status_code, 422)

    def test_trims_question_and_forwards_language_and_jurisdiction(self):
        with patch.object(groq_llm, "generate_answer", new_callable=AsyncMock, return_value="A grounded answer") as generate:
            data = self.query(query="  What is TRIPS?  ", jurisdiction="INTERNATIONAL", language="hi").json()
            self.assertEqual(data["query"], "What is TRIPS?")
            self.assertEqual(generate.call_args.kwargs["jurisdiction"], "INTERNATIONAL")
            self.assertEqual(generate.call_args.kwargs["language"], "hi")
            self.assertIn("selected jurisdiction", SYSTEM_PROMPT)

    def test_no_registered_or_responding_service_returns_503(self):
        self.assertEqual(self.query(target_rags=["not_registered"]).status_code, 503)
        connector = rag_registry.get("rag2_legal_regulatory")
        with patch.object(connector, "query", new_callable=AsyncMock, side_effect=RuntimeError("offline")):
            self.assertEqual(self.query(target_rags=[connector.rag_id]).status_code, 503)

    def test_local_frontend_cors_preflight(self):
        response = self.client.options("/api/v1/orchestrator/query", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


if __name__ == "__main__":
    unittest.main()
