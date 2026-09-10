"""Conflict detection and legal resolution engine for RAG 2."""
import logging
from typing import List, Tuple, Dict, Any, Optional
from app.rag2.models import LegalEvidenceChunk

logger = logging.getLogger(__name__)


class LegalConflictEngine:
    """
    Identifies statutory and regulatory tensions among retrieved legal provisions
    and provides resolved legal conclusions based on statutory precedence and hierarchy.
    """

    KNOWN_TENSIONS = [
        {
            "id": "NTC_VS_SECTION_6_IPR",
            "trigger_terms": ["section 40", "normally traded commodities", "ntc", "section 6", "patent application"],
            "description": (
                "Statutory Tension: Section 40 NTC exemption vs Section 6 mandatory IPR approval. "
                "Resolution: Central Government NTC exemption under Section 40 applies strictly to local trade and direct consumption. "
                "Section 6(1) remains mandatory when seeking intellectual property rights on inventions derived from biological resources."
            )
        },
        {
            "id": "TK_BAR_VS_HERBAL_NOVELTY",
            "trigger_terms": ["traditional knowledge", "section 3(p)", "admixture", "section 3(e)", "novel formulation"],
            "description": (
                "Statutory Exclusion: Section 3(p) vs Section 3(e) Synergism requirement. "
                "Resolution: Pure extraction or classical preparation is excluded under Section 3(p). "
                "To overcome this statutory bar, the applicant must establish unexpected synergism (Section 3(e)) with experimental evidence."
            )
        }
    ]

    def check_conflicts(self, chunks: List[LegalEvidenceChunk], query: str) -> Tuple[bool, Optional[str]]:
        """
        Analyzes retrieved chunks for apparent contradictions or statutory qualifications.
        Returns: (conflict_detected, conflict_resolution_explanation)
        """
        combined_text = (query + " " + " ".join(c.text[:200] for c in chunks)).lower()

        for tension in self.KNOWN_TENSIONS:
            match_count = sum(1 for term in tension["trigger_terms"] if term in combined_text)
            if match_count >= 2:
                return True, tension["description"]

        # Check for authority tier discrepancies (e.g. TIER_1 vs TIER_2/3)
        tiers = set(c.authority_tier for c in chunks)
        if len(tiers) > 1 and "TIER_1_AUTHORITATIVE" in tiers:
            return False, "Evidence set contains Tier 1 authoritative statutes; lower tiers are treated as supporting only."

        return False, None


conflict_engine = LegalConflictEngine()
