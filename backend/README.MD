RAG 1: AYURVEDA + INTELLECTUAL PROPERTY KNOWLEDGE

PURPOSE
-------
RAG 1 is the domain knowledge layer of IP-SAKTI.

It provides contextual knowledge about:

- Ayurveda
- Ayurvedic medicine
- Ayurvedic formulations
- Medicinal plants and ingredients
- Classical Ayurvedic texts and formulations
- Traditional Ayurvedic knowledge
- Traditional Knowledge Digital Library (TKDL) concepts
- Traditional knowledge concepts
- Intellectual property concepts
- Patents
- Prior art
- Trademarks
- Geographical indications
- Designs
- Copyright
- Trade secrets
- Ayurveda/IP terminology and relationships

CORE RESPONSIBILITY
-------------------
RAG 1 answers:

"What is this concept?"
"How are Ayurveda and IP concepts related?"
"What does this Ayurveda/IP terminology mean?"

RAG 1 does NOT make the final legal or regulatory decision.

For authoritative legal conclusions, the system must use RAG 2.


EXAMPLES
--------
Question:
"What is a classical Ayurvedic formulation?"

→ RAG 1

Question:
"What is prior art?"

→ RAG 1

Question:
"What is TKDL?"

→ RAG 1

Question:
"How can an Ayurvedic product be protected using IP?"

→ RAG 1 for conceptual knowledge,
  RAG 2 for the authoritative legal position.


DATA CATEGORIES
---------------
AYURVEDA
- Ayurvedic concepts
- Formulations
- Ingredients
- Medicinal plants
- Traditional uses
- Classical references
- Preparation methods
- Ayurvedic terminology
- Traditional knowledge

INTELLECTUAL PROPERTY
- Patent concepts
- Prior-art concepts
- Trademark concepts
- GI concepts
- Design concepts
- Copyright concepts
- Trade-secret concepts
- IP terminology


DATA SOURCES
------------
Use curated and trustworthy domain sources.

AYURVEDA SOURCES
- Official AYUSH publications
- Authoritative Ayurvedic references
- Pharmacopoeial / formulary material where permitted
- Traditional knowledge resources
- Academic/public-domain Ayurveda resources

IP KNOWLEDGE SOURCES
- WIPO educational/reference material
- Official IP terminology/reference material
- Official patent/trademark/GI explanatory sources
- Authoritative IP publications


DATA INGESTION PIPELINE
-----------------------
Source
  ↓
Fetcher / Downloader
  ↓
Parser
  ↓
Cleaning
  ↓
Deduplication
  ↓
Language Detection
  ↓
Metadata Extraction
  ↓
Semantic Chunking
  ↓
Embedding Generation
  ↓
Vector Index
  +
Keyword Index


CHUNKING STRATEGY
-----------------
Do not blindly split documents into fixed-size chunks.

Prefer semantic/domain boundaries.

Example:

Ayurveda document
 ├── Concept
 ├── Ingredient
 ├── Formulation
 ├── Preparation
 └── Traditional use

IP document
 ├── Definition
 ├── Concept
 ├── Example
 └── Explanation


METADATA
--------
Each chunk should contain:

{
  "chunk_id": "RAG1-000001",
  "document_id": "DOC-001",
  "domain": "AYURVEDA",
  "subdomain": "FORMULATION",
  "topic": "CLASSICAL_FORMULATION",
  "language": "en",
  "title": "...",
  "source_name": "...",
  "source_url": "...",
  "document_version": "...",
  "published_at": "...",
  "content_hash": "..."
}

Recommended domains:

AYURVEDA
TRADITIONAL_KNOWLEDGE
FORMULATION
INGREDIENT
PATENT
PRIOR_ART
TRADEMARK
GEOGRAPHICAL_INDICATION
DESIGN
COPYRIGHT
TRADE_SECRET


RETRIEVAL
---------
Use hybrid retrieval.

                 Query
                   ↓
            Language Detection
                   ↓
             Domain Filter
                   ↓
       +-----------+-----------+
       |                       |
       ↓                       ↓
  Vector Search              BM25
       |                       |
       +-----------+-----------+
                   ↓
                 Fusion
                   ↓
                Reranker
                   ↓
               Top 5–10
                   ↓
               RAG Context


MULTILINGUAL RETRIEVAL
----------------------
User language
      ↓
Language Detection
      ↓
Domain/technical-term normalization
      ↓
Language-independent concept
      ↓
Hybrid Retrieval
      ↓
Relevant evidence
      ↓
Response in requested language

Example:

"पूर्व कला"
"Prior Art"
"prior-art"
"Hinglish equivalent"

        ↓

     PRIOR_ART


OUTPUT
------
RAG 1 returns domain evidence/context.

Example:

{
  "query": "...",
  "language": "en",
  "answer_context": "...",
  "evidence": [
    {
      "document_id": "DOC-001",
      "chunk_id": "RAG1-000001",
      "title": "...",
      "source_name": "...",
      "source_url": "..."
    }
  ],
  "retrieval_score": 0.91
}


API
---
POST /api/v1/rag/knowledge/query

POST /api/v1/rag/knowledge/search

GET /api/v1/rag/knowledge/health


STORAGE
-------
PostgreSQL
  ↓
Metadata

pgvector / Vector DB
  ↓
Embeddings

BM25 / OpenSearch
  ↓
Keyword index

Object Storage
  ↓
Original source documents


EVALUATION
----------
Retrieval:
- Recall@K
- Precision@K
- MRR
- NDCG

Domain QA:
- Domain correctness
- Grounding
- Unsupported-claim rate

Multilingual:
- Intent preservation
- Technical terminology preservation
- Retrieval performance by language


INTEGRATION
-----------
RAG 1
  ↓
Ayurveda + IP domain context
  ↓
Main Orchestrator
  ↓
RAG 2
  ↓
Legal + Regulatory Evidence
  ↓
Rule Engine
  ↓
Citation Verification
  ↓
Final Response


CORE PRINCIPLE
--------------
RAG 1 = Domain knowledge

RAG 1 explains concepts.
RAG 1 provides context.
RAG 1 does not independently determine legal applicability.


================================================================================
RAG 2: LEGAL + REGULATORY EVIDENCE LAYER
================================================================================

PURPOSE & ARCHITECTURE
----------------------
RAG 2 is the authoritative statutory evidence retrieval layer of IP-SAKTI.
It indexes 2,527 authoritative legal chunks across:
- The Patents Act, 1970 (Section 3(p) TK bar, Section 3(e) synergism, Section 3(d), etc.)
- The Biological Diversity Act, 2002 (Section 6 mandatory IPR approval, Section 40 NTC, Section 55 penalties)
- The Biological Diversity Rules, 2004 & NBA ABS Guidelines 2014
- The Drugs and Cosmetics Act, 1940 & Rules, 1945 (Ayurvedic/Siddha/Unani drug provisions)
- Food Safety and Standards (Ayurveda Aahara) Regulations, 2022
- Trade Marks Act 1999, GI of Goods Act 1999, Designs Act 2000, PPV&FR Act 2001, DMR Act 1954
- International treaties: TRIPS Agreement, CBD, Nagoya Protocol, WIPO GRATK Treaty (2024)

RETRIEVAL PIPELINE
------------------
1. Multilingual query normalization (Hindi, Hinglish, English)
2. Hybrid search: BM25 (optimized for section/rule numbers) + Dense Semantic Vector Search (sublinear TF-IDF n-grams)
3. Reciprocal Rank Fusion (RRF) with Section Priority Reranking
4. Point-in-time / Historical version validity engine (effective_from <= date <= effective_to)
5. Conflict detection (e.g. Section 40 NTC vs Section 6 IPR mandatory approval)
6. Citation-first synthesizer ensuring zero hallucinated citations

REST API ENDPOINTS
------------------
- POST /api/v1/rag/legal/query : Authoritative legal question answering with citations
- POST /api/v1/rag/legal/historical : Historical point-in-time legal validity check
- POST /api/v1/rag/legal/search : Granular statutory search (hybrid, bm25, vector)
- GET /api/v1/rag/legal/documents/{document_id} : Document metadata and chunk inspection
- GET /api/v1/rag/legal/health : Health status, chunk counts, and indexed categories