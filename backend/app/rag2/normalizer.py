"""Multilingual normalization and legal concept expansion for RAG 2."""
import re
from typing import Tuple, List, Dict, Optional, Any

# Legal normalization dictionary mapping Hindi / Hinglish terms to statutory concepts
LEGAL_TERM_MAP: Dict[str, Dict[str, Any]] = {
    # Section 3(p) / Traditional Knowledge
    "धारा 3(p)": {"canonical": "Section 3(p) Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge", "patents act"], "category": "patents_act"},
    "dhara 3(p)": {"canonical": "Section 3(p) Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},
    "dhara 3p": {"canonical": "Section 3(p) Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},
    "3p": {"canonical": "Section 3(p) Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},
    "traditional knowledge": {"canonical": "Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},
    "paramparik gyan": {"canonical": "Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},
    "पारंपरिक ज्ञान": {"canonical": "Traditional Knowledge Bar", "tokens": ["section 3(p)", "traditional knowledge"], "category": "patents_act"},

    # Section 3(e) / Admixture
    "धारा 3(e)": {"canonical": "Section 3(e) Mere Admixture", "tokens": ["section 3(e)", "mere admixture", "synergism"], "category": "patents_act"},
    "dhara 3(e)": {"canonical": "Section 3(e) Mere Admixture", "tokens": ["section 3(e)", "mere admixture", "synergism"], "category": "patents_act"},
    "dhara 3e": {"canonical": "Section 3(e) Mere Admixture", "tokens": ["section 3(e)", "mere admixture", "synergism"], "category": "patents_act"},
    "admixture": {"canonical": "Section 3(e) Mere Admixture", "tokens": ["section 3(e)", "admixture", "synergism"], "category": "patents_act"},
    "synergism": {"canonical": "Synergism Requirement", "tokens": ["section 3(e)", "synergy", "synergism"], "category": "patents_act"},

    # Biodiversity Act Section 6 & NBA
    "धारा 6": {"canonical": "Section 6 Biological Diversity Act", "tokens": ["section 6", "national biodiversity authority", "prior approval"], "category": "biodiversity_act"},
    "dhara 6": {"canonical": "Section 6 Biological Diversity Act", "tokens": ["section 6", "national biodiversity authority", "prior approval"], "category": "biodiversity_act"},
    "nba approval": {"canonical": "National Biodiversity Authority Approval", "tokens": ["section 6", "national biodiversity authority", "form iii"], "category": "biodiversity_act"},
    "nba anumati": {"canonical": "National Biodiversity Authority Approval", "tokens": ["section 6", "nba", "approval"], "category": "biodiversity_act"},
    "एनबीए अनुमति": {"canonical": "National Biodiversity Authority Approval", "tokens": ["section 6", "nba", "approval"], "category": "biodiversity_act"},
    "जैव विविधता": {"canonical": "Biological Diversity Act", "tokens": ["biological diversity act", "nba", "benefit sharing"], "category": "biodiversity_act"},
    "jaiv vividhta": {"canonical": "Biological Diversity Act", "tokens": ["biological diversity act", "nba"], "category": "biodiversity_act"},
    "biodiversity": {"canonical": "Biological Diversity Act", "tokens": ["biological diversity act", "nba", "section 6"], "category": "biodiversity_act"},

    # Benefit Sharing / ABS
    "लाभ साझाकरण": {"canonical": "Access and Benefit Sharing", "tokens": ["benefit sharing", "abs regulations", "gross sales"], "category": "nba_abs_guidelines"},
    "benefit sharing": {"canonical": "Access and Benefit Sharing", "tokens": ["benefit sharing", "abs", "guidelines 2014"], "category": "nba_abs_guidelines"},
    "abs": {"canonical": "Access and Benefit Sharing", "tokens": ["access and benefit sharing", "guidelines 2014", "nba"], "category": "nba_abs_guidelines"},

    # Ayurveda Aahara / Food
    "आयुर्वेद आहार": {"canonical": "Ayurveda Aahara Regulations", "tokens": ["ayurveda aahara", "fssai", "regulations 2022"], "category": "fssai_ayurveda_aahar"},
    "ayurveda aahar": {"canonical": "Ayurveda Aahara Regulations", "tokens": ["ayurveda aahara", "fssai", "food safety"], "category": "fssai_ayurveda_aahar"},
    "ayurveda aahara": {"canonical": "Ayurveda Aahara Regulations", "tokens": ["ayurveda aahara", "fssai regulations 2022"], "category": "fssai_ayurveda_aahar"},

    # Drugs & Cosmetics Act (AYUSH rules)
    "औषधि नियम": {"canonical": "Drugs and Cosmetics Act & Rules", "tokens": ["drugs and cosmetics act 1940", "rules 1945", "ayurvedic drug"], "category": "drugs_cosmetics_act"},
    "ayurvedic drug": {"canonical": "Ayurvedic Drug Regulation", "tokens": ["drugs and cosmetics act", "rules 1945", "ayurvedic"], "category": "drugs_cosmetics_act"},
    "d&c act": {"canonical": "Drugs and Cosmetics Act", "tokens": ["drugs and cosmetics act 1940", "rules 1945"], "category": "drugs_cosmetics_act"},

    # Trademarks & GI
    "ट्रेडमार्क": {"canonical": "Trade Marks Act", "tokens": ["trade marks act 1999", "trademark"], "category": "trademarks_act"},
    "trademark": {"canonical": "Trade Marks Act", "tokens": ["trade marks act 1999"], "category": "trademarks_act"},
    "geographical indication": {"canonical": "GI Act", "tokens": ["geographical indications goods act 1999", "gi"], "category": "gi_act"},
    "gi tag": {"canonical": "GI Act", "tokens": ["geographical indications goods act 1999"], "category": "gi_act"},

    # Plant Variety
    "पौधा किस्म": {"canonical": "PPVFR Act", "tokens": ["protection of plant varieties farmers rights 2001"], "category": "ppvfr_act"},
    "plant variety": {"canonical": "PPVFR Act", "tokens": ["protection of plant varieties farmers rights 2001"], "category": "ppvfr_act"},

    # Treaties
    "trips": {"canonical": "TRIPS Agreement", "tokens": ["trips agreement", "article 27"], "category": "trips"},
    "wipo": {"canonical": "WIPO Treaty", "tokens": ["wipo treaty genetic resources traditional knowledge 2024"], "category": "wipo_gratk"},
    "nagoya": {"canonical": "Nagoya Protocol", "tokens": ["nagoya protocol access benefit sharing"], "category": "nagoya_protocol"}
}


def normalize_legal_query(query: str) -> Tuple[str, Optional[str], List[str]]:
    """
    Analyzes legal query, expands tokens, and suggests target category if mapped.
    Returns: (expanded_query, suggested_category, matched_concepts)
    """
    q_lower = query.lower().strip()
    expanded_tokens = [query]
    suggested_category = None
    matched_concepts = []

    for term, data in LEGAL_TERM_MAP.items():
        if term in q_lower:
            matched_concepts.append(data["canonical"])
            expanded_tokens.extend(data["tokens"])
            if not suggested_category:
                suggested_category = data["category"]

    expanded_query = " ".join(dict.fromkeys(expanded_tokens))
    return expanded_query, suggested_category, matched_concepts

