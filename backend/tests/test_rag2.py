"""Comprehensive unit and functional tests for RAG 2 (Legal & Regulatory Evidence)."""
import unittest
from app.rag2.ingestion import ingest_legal_knowledge_base, extract_legal_hierarchy
from app.rag2.service import rag2_service
from app.rag2.models import (
    LegalQueryRequest,
    HistoricalQueryRequest,
    LegalSearchRequest
)
from app.rag2.normalizer import normalize_legal_query
from app.rag2.versioning import is_chunk_applicable_at_date
from app.rag2.conflict import conflict_engine


class TestRAG2Pipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rag2_service.initialize()

    def test_dataset_ingestion_and_counts(self):
        chunks = rag2_service.chunks
        self.assertGreaterEqual(len(chunks), 2000)
        categories = set(c.category for c in chunks)
        self.assertIn("patents_act", categories)
        self.assertIn("biodiversity_act", categories)
        self.assertIn("drugs_cosmetics_act", categories)
        self.assertIn("fssai_ayurveda_aahar", categories)
        self.assertIn("trademarks_act", categories)
        self.assertIn("trips", categories)

    def test_legal_section_extraction(self):
        # Section 3(p) in patents act
        tk_text = "(p) an invention which, in effect, is traditional knowledge or aggregation of known properties."
        meta1 = extract_legal_hierarchy(tk_text, "patents_act")
        self.assertEqual(meta1["section"], "3(p)")

        # Section 3(e) in patents act
        admix_text = "(e) a substance obtained by a mere admixture resulting only in the aggregation of the properties"
        meta2 = extract_legal_hierarchy(admix_text, "patents_act")
        self.assertEqual(meta2["section"], "3(e)")

        # Section 6 in biodiversity act
        nba_text = "6. (1) No person shall apply for any intellectual property right without previous approval"
        meta3 = extract_legal_hierarchy(nba_text, "biodiversity_act")
        self.assertEqual(meta3["section"], "6")

    def test_bm25_and_hybrid_section_query(self):
        req = LegalQueryRequest(query="Section 3(p) traditional knowledge bar on patentability", top_k=3)
        res = rag2_service.query(req)
        self.assertEqual(res.jurisdiction, "INDIA")
        self.assertGreater(len(res.citations), 0)
        # Check that top citation is Section 3(p) or Patents Act
        top_cit = res.citations[0]
        self.assertEqual(top_cit.document_id, "PATENTS_ACT_1970")
        self.assertEqual(top_cit.section, "3(p)")

    def test_section_6_biodiversity_query(self):
        req = LegalQueryRequest(query="Section 6 approval from National Biodiversity Authority for patent", top_k=3)
        res = rag2_service.query(req)
        self.assertGreater(len(res.citations), 0)
        top_cit = res.citations[0]
        self.assertEqual(top_cit.document_id, "BIODIVERSITY_ACT_2002")
        self.assertEqual(top_cit.section, "6")

    def test_fssai_ayurveda_aahara_query(self):
        req = LegalQueryRequest(query="Ayurveda Aahara regulations food safety standards", top_k=3)
        res = rag2_service.query(req)
        self.assertGreater(len(res.citations), 0)
        found_aahar = any("aahar" in c.title.lower() or "fssai" in c.document_id.lower() for c in res.citations)
        self.assertTrue(found_aahar)

    def test_multilingual_normalization(self):
        expanded, cat, concepts = normalize_legal_query("धारा 3(p) पारंपरिक ज्ञान")
        self.assertEqual(cat, "patents_act")
        self.assertIn("Section 3(p) Traditional Knowledge Bar", concepts)
        self.assertIn("section 3(p)", expanded.lower())

        expanded2, cat2, concepts2 = normalize_legal_query("nba approval jaiv vividhta")
        self.assertEqual(cat2, "biodiversity_act")

    def test_historical_point_in_time_filtering(self):
        chunks = rag2_service.chunks
        bd_chunk = next(c for c in chunks if c.category == "biodiversity_act")

        # In 1995: BD Act 2002 was not in force
        is_app_1995, reason_1995 = is_chunk_applicable_at_date(bd_chunk, "1995-01-01")
        self.assertFalse(is_app_1995)
        self.assertIn("Not yet in force", reason_1995)

        # In 2020: BD Act 2002 is in force
        is_app_2020, reason_2020 = is_chunk_applicable_at_date(bd_chunk, "2020-01-01")
        self.assertTrue(is_app_2020)

    def test_conflict_detection_engine(self):
        conflict_detected, expl = conflict_engine.check_conflicts([], "Normally Traded Commodities section 40 exemption and patent application section 6")
        self.assertTrue(conflict_detected)
        self.assertIn("Section 40", expl)
        self.assertIn("Section 6", expl)

    def test_search_modes(self):
        for mode in ["hybrid", "bm25", "vector"]:
            req = LegalSearchRequest(query="Section 6 National Biodiversity Authority", mode=mode, top_k=3)
            res = rag2_service.search(req)
            self.assertEqual(res.mode, mode)
            self.assertGreater(len(res.results), 0)

    def test_health_check(self):
        health = rag2_service.health()
        self.assertEqual(health.status, "healthy")
        self.assertEqual(health.rag_id, "RAG2_LEGAL_REGULATORY")
        self.assertGreater(health.total_chunks, 2000)
        self.assertIn("patents_act", health.categories_indexed)


if __name__ == "__main__":
    unittest.main()
