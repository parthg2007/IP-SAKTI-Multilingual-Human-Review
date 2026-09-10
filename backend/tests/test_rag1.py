"""Unit and integration tests for RAG 1 Domain Knowledge service."""
import unittest
from app.rag1.service import RAG1Service
from app.data.models import RAGQueryRequest, RAGSearchRequest
from app.core.language import detect_language, normalize_and_expand_query
from app.data.ingestion import ingest_knowledge_base


class TestRAG1Pipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = RAG1Service()
        cls.service.initialize()

    def test_dataset_ingestion(self):
        chunks = ingest_knowledge_base()
        self.assertGreater(len(chunks), 0)
        first = chunks[0]
        self.assertTrue(first.chunk_id.startswith("RAG1-"))
        self.assertTrue(first.document_id.startswith("DOC-"))
        self.assertIsNotNone(first.title)
        self.assertIsNotNone(first.text)
        self.assertIsNotNone(first.source_name)

    def test_language_detection(self):
        self.assertEqual(detect_language("What is TKDL?"), "en")
        self.assertEqual(detect_language("पूर्व कला क्या है?"), "hi")
        self.assertEqual(detect_language("Ayurvedic formulation ka patent kaise lein?"), "hi-Latn")

    def test_term_normalization(self):
        enriched, concepts, domains = normalize_and_expand_query("पूर्व कला")
        self.assertTrue(any("Prior Art" in c for c in concepts))

        enriched, concepts, domains = normalize_and_expand_query("section 3(p) patent")
        self.assertTrue(any("3(p)" in c for c in concepts))

    def test_query_api_conformance(self):
        req = RAGQueryRequest(query="What is the Traditional Knowledge Digital Library (TKDL)?", top_k=3)
        res = self.service.query(req)

        self.assertEqual(res.query, req.query)
        self.assertEqual(res.language, "en")
        self.assertGreater(len(res.evidence), 0)
        self.assertGreater(res.retrieval_score, 0.0)
        self.assertIn("RAG 1", res.answer_context)

        # Check evidence item schema from README
        ev = res.evidence[0]
        self.assertIsNotNone(ev.document_id)
        self.assertIsNotNone(ev.chunk_id)
        self.assertIsNotNone(ev.title)
        self.assertIsNotNone(ev.source_name)

    def test_multilingual_query(self):
        req = RAGQueryRequest(query="पूर्व कला क्या है?", top_k=3)
        res = self.service.query(req)
        self.assertEqual(res.language, "hi")
        self.assertGreater(len(res.evidence), 0)

    def test_search_modes(self):
        for mode in ["hybrid", "vector", "bm25"]:
            req = RAGSearchRequest(query="Section 6 National Biodiversity Authority approval", mode=mode, top_k=3)
            res = self.service.search(req)
            self.assertEqual(res.mode, mode)
            self.assertGreater(res.total_hits, 0)
            self.assertGreater(len(res.results), 0)

    def test_health_check(self):
        health = self.service.health()
        self.assertEqual(health.status, "healthy")
        self.assertEqual(health.rag_id, "RAG1_AYURVEDA_IP")
        self.assertGreater(health.total_chunks, 50)
        self.assertIn("Statutory Law", health.domains_indexed)


if __name__ == "__main__":
    unittest.main()
