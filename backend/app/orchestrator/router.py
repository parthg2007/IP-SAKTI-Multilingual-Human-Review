"""Intelligent query router for dispatching queries between RAG 1, RAG 2, or both."""
import re
from typing import List, Tuple
from app.data.models import RAGRouteDecision

# Patterns indicating purely conceptual / domain knowledge queries
CONCEPTUAL_PATTERNS = [
    r"\bwhat\s+is\b", r"\bdefine\b", r"\bmeaning\s+of\b", r"\bexplain\b",
    r"\boverview\b", r"\bkya\s+hai\b", r"\bkaise\s+samjhein\b",
    r"\bwhat\s+does\s+.*\s+mean\b", r"\bhistory\s+of\b", r"\bwho\s+created\b"
]

# Patterns indicating legal decision / statutory enforcement / compliance queries
LEGAL_DECISION_PATTERNS = [
    r"\bpenalty\b", r"\bpunishment\b", r"\bcriminal\s+liability\b", r"\bappeal\b",
    r"\bstatutory\s+fee\b", r"\bsection\s+55\b", r"\bprosecution\b", r"\bcourt\b",
    r"\blegal\s+validity\b", r"\benforceability\b", r"\bjudgement\b",
    r"\bsection\s+3\([a-z]\)\b", r"\bsection\s+6\b", r"\bsection\s+40\b",
    r"\bd&c\s+act\b", r"\bdrugs\s+and\s+cosmetics\b", r"\brule\s+161\b"
]

# Patterns indicating intersection / hybrid queries (both conceptual domain + legal position)
HYBRID_PATTERNS = [
    r"\bhow\s+can\b.*\bprotect\b", r"\bcan\s+.*\bpatent\b", r"\bhow\s+to\s+patent\b",
    r"\bprotect.*\busing\s+ip\b", r"\bcommercialize\b", r"\bpatentability\b",
    r"\bcompliance\s+for\b", r"\brequirement\s+for\b", r"\bhow\s+are\s+.*related\b",
    r"\bapply\s+for\s+patent\b", r"\bpermission\s+needed\b", r"\bpatented\b",
    r"\bbiodiversity\s+approval\b", r"\bcan\s+i\s+trademark\b", r"\bip\s+protection\b"
]


class QueryRouter:
    """
    Analyzes intent of user query to determine whether to query:
    - RAG 1 only (Conceptual domain knowledge)
    - RAG 2 only (Statutory compliance & legal conclusions)
    - Both RAG 1 and RAG 2 (Integrated domain knowledge + authoritative legal framework)
    """

    def route(self, query: str) -> RAGRouteDecision:
        q_lower = query.lower().strip()

        # Check hybrid pattern first
        for pat in HYBRID_PATTERNS:
            if re.search(pat, q_lower):
                return RAGRouteDecision(
                    target_rags=["rag1_domain_knowledge", "rag2_legal_regulatory"],
                    primary_rag="rag1_domain_knowledge",
                    intent="hybrid_domain_and_legal",
                    confidence=0.92,
                    explanation="Query requires domain conceptual knowledge from RAG 1 and authoritative legal standing from RAG 2."
                )

        # Check pure legal pattern
        for pat in LEGAL_DECISION_PATTERNS:
            if re.search(pat, q_lower):
                return RAGRouteDecision(
                    target_rags=["rag2_legal_regulatory"],
                    primary_rag="rag2_legal_regulatory",
                    intent="authoritative_legal_statute",
                    confidence=0.88,
                    explanation="Query involves statutory enforcement, penalties, or authoritative legal determinations handled by RAG 2."
                )

        # Check pure conceptual pattern
        for pat in CONCEPTUAL_PATTERNS:
            if re.search(pat, q_lower):
                return RAGRouteDecision(
                    target_rags=["rag1_domain_knowledge"],
                    primary_rag="rag1_domain_knowledge",
                    intent="conceptual_domain_knowledge",
                    confidence=0.90,
                    explanation="Query asks for concept definitions, classical terminology, or domain explanations handled by RAG 1."
                )

        # Default heuristic: if mentions patent/law/compliance alongside ayurveda/traditional knowledge, use both
        legal_terms = ["patent", "patented", "law", "act", "section", "approval", "nba", "abs", "bar", "statut", "regulation", "fssai", "trademark", "gi", "design", "penalty"]
        domain_terms = ["ayurved", "formulation", "herb", "tkdl", "plant", "traditional", "prior art", "classical", "turmeric", "neem", "ashwagandha", "pepper", "aahara"]

        has_legal_terms = any(term in q_lower for term in legal_terms)
        has_domain_terms = any(term in q_lower for term in domain_terms)

        if has_legal_terms and has_domain_terms:
            return RAGRouteDecision(
                target_rags=["rag1_domain_knowledge", "rag2_legal_regulatory"],
                primary_rag="rag1_domain_knowledge",
                intent="hybrid_domain_and_legal",
                confidence=0.88,
                explanation="Query touches on both Ayurveda domain concepts and patent/biodiversity statutory requirements."
            )

        if has_legal_terms:
            return RAGRouteDecision(
                target_rags=["rag2_legal_regulatory"],
                primary_rag="rag2_legal_regulatory",
                intent="authoritative_legal_statute",
                confidence=0.82,
                explanation="Query focuses primarily on statutory, regulatory, or compliance provisions."
            )

        # Fallback to RAG 1 domain context
        return RAGRouteDecision(
            target_rags=["rag1_domain_knowledge"],
            primary_rag="rag1_domain_knowledge",
            intent="domain_context_default",
            confidence=0.75,
            explanation="Defaulted to RAG 1 domain context layer."
        )


query_router = QueryRouter()
