# RAG-2: Legal + Regulatory Evidence RAG

## Purpose

This RAG is the **authoritative evidence retrieval layer** for SIH26045.

It handles:

- Indian IP laws
- rules and regulations
- AYUSH regulations
- biodiversity / ABS provisions
- official government notifications
- treaties
- international IP frameworks
- official registry information
- relevant case law
- amendments and historical versions

Its purpose is to retrieve the **exact authoritative evidence** required to support an IP or regulatory conclusion.

---

## Core Responsibility

```text
Structured User Query
        ↓
Jurisdiction / IP / Product filters
        ↓
Legal + Regulatory Evidence RAG
        ↓
Relevant provisions / records
        ↓
Rule Engine
        ↓
Citation-backed conclusion
```

This RAG should be treated as the primary evidence source for legal/regulatory claims.

---

## What This RAG Is Not

It should not contain general web content indiscriminately.

Do not build:

```text
Entire Internet
      ↓
Vector DB
```

Instead build:

```text
Curated authoritative corpus
      ↓
Versioned legal evidence index
```

The original source documents remain the source of truth.

---

## Source Hierarchy

### Tier 1 — Authoritative

Examples:

```text
India Code
IP India
Official AYUSH sources
Official government departments
WIPO
WTO / TRIPS
Official treaty repositories
Official regulatory / registry sources
```

### Tier 2 — Supporting

Official explanatory documents and guidance.

### Tier 3 — Discovery only

Third-party material may help discover a source but should not normally be used as the evidence supporting a legal conclusion.

---

## Data Pipeline

```text
Approved Source
      ↓
Fetch / Crawl
      ↓
Document Validation
      ↓
Parse PDF / HTML
      ↓
Clean
      ↓
Deduplicate
      ↓
Detect amendment/version
      ↓
Extract legal hierarchy
      ↓
Semantic chunking
      ↓
Metadata enrichment
      ↓
Embedding
      +
BM25 index
      ↓
Version-aware index
```

---

## Legal Document Structure

Preserve hierarchy.

```text
Act
 └── Chapter
      └── Section
           └── Subsection
                └── Clause
```

For regulations:

```text
Regulation
 └── Rule
      └── Sub-rule
           └── Clause
```

For treaties:

```text
Treaty
 └── Article
      └── Paragraph
```

This enables exact citations.

---

## Metadata

Every legal chunk should have provenance.

```json
{
  "chunk_id": "PATENTS_3_P_001",
  "document_id": "PATENTS_ACT",
  "title": "Patents Act",
  "source": "India Code",
  "source_url": "...",
  "jurisdiction": "INDIA",
  "domain": "PATENT",
  "document_type": "STATUTE",
  "section": "3(p)",
  "version": "2026",
  "effective_from": "...",
  "effective_to": null,
  "language": "en",
  "content_hash": "sha256..."
}
```

Required metadata:

```text
jurisdiction
domain
document_type
section/article/rule
version
effective_from
effective_to
source
source_url
authority_level
language
content_hash
```

---

## Version-Aware Retrieval

Do not treat every version as equally current.

Store:

```text
Patents Act
 ├── 2022
 ├── 2024
 ├── 2025
 └── 2026 ← current
```

Normal query:

```text
status = CURRENT
```

Historical query:

```text
effective_from <= requested_date
effective_to   >= requested_date
```

This allows questions such as:

> "What was applicable in 2023?"

without incorrectly returning the 2026 version.

---

## Retrieval Architecture

Use hierarchical filtering first.

```text
Query
  ↓
Jurisdiction
  ↓
IP / regulatory category
  ↓
Product type
  ↓
Current / historical version
  ↓
Candidate documents
  ↓
Hybrid retrieval
  ↓
Reranker
  ↓
Top 5–15 evidence chunks
```

Hybrid search:

```text
Semantic Vector Search
          +
BM25 / Exact Keyword Search
          ↓
       Fusion
          ↓
      Reranker
```

Exact legal references such as:

```text
Section 3(p)
Article 33
Rule 6
Patents Act
TRIPS
```

should be easy to retrieve.

---

## Citation-First Design

Every generated legal claim must be connected to evidence.

```text
Claim
 ↓
Supporting chunk
 ↓
Document
 ↓
Section / Article
 ↓
Source URL
 ↓
Version / effective date
```

Example:

```json
{
  "claim": "....",
  "citation": {
    "document": "Patents Act",
    "section": "3(p)",
    "source": "India Code",
    "version": "2026",
    "chunk_id": "..."
  }
}
```

The system should never allow the LLM to invent a citation.

---

## Conflict Detection

If retrieved documents disagree:

```text
Source A
Rule X
Version 2024

Source B
Rule Y
Version 2026
```

run:

```text
Conflict detected
      ↓
Compare authority
      ↓
Compare effective dates
      ↓
Determine active provision
      ↓
Return current evidence
```

If the conflict cannot be resolved confidently:

```text
ABSTAIN / FLAG FOR REVIEW
```

---

## Legal RAG Retrieval Example

Query:

> "Can I patent this Ayurvedic formulation in India?"

Structured query:

```json
{
  "jurisdiction": "INDIA",
  "domains": [
    "PATENT",
    "TRADITIONAL_KNOWLEDGE",
    "BIODIVERSITY",
    "AYUSH"
  ],
  "intent": "PATENTABILITY"
}
```

Retrieval:

```text
India Code
    +
IP India
    +
AYUSH
    +
Biodiversity sources
    ↓
Relevant sections
    ↓
Reranker
    ↓
Evidence set
```

The RAG returns evidence to the decision engine.

---

## API

### Query evidence

```http
POST /api/v1/rag/legal/query
```

Request:

```json
{
  "query": "Can I patent this Ayurvedic formulation in India?",
  "jurisdiction": "INDIA",
  "domain": [
    "PATENT",
    "AYURVEDA",
    "BIODIVERSITY"
  ],
  "temporal_mode": "CURRENT"
}
```

### Historical search

```http
POST /api/v1/rag/legal/historical
```

### Direct document search

```http
POST /api/v1/rag/legal/search
```

### Source lookup

```http
GET /api/v1/rag/legal/documents/{document_id}
```

---

## Response Contract

```json
{
  "query": "...",
  "evidence": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "title": "...",
      "section": "...",
      "text": "...",
      "source_url": "...",
      "version": "...",
      "effective_from": "..."
    }
  ],
  "retrieval_metadata": {
    "jurisdiction": "INDIA",
    "domains": ["PATENT", "AYUSH"],
    "retrieval_method": "HYBRID"
  }
}
```

---

## Storage

Recommended architecture:

```text
                    Legal Knowledge Base
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
     PostgreSQL         pgvector         BM25 Index
     metadata           embeddings       keywords
          |
          v
     Object Storage
     original documents
```

PostgreSQL should remain the authoritative metadata store.

---

## Why This RAG Is Separate From RAG-1

The separation is intentional.

### RAG-1

```text
"What is this?"
"What does this concept mean?"
"How are Ayurveda and IP related?"
```

Provides domain knowledge.

### RAG-2

```text
"What does the applicable law/regulation actually say?"
"Which section applies?"
"What is the current provision?"
```

Provides authoritative legal evidence.

The main backend combines both:

```text
User
 ↓
Query Router
 ↓
 ┌───────────────────────┐
 │                       │
 ↓                       ↓
RAG-1                  RAG-2
Domain                 Legal Evidence
Knowledge              Authority
 │                       │
 └───────────┬───────────┘
             ↓
        Rule Engine
             ↓
      Citation Validator
             ↓
       Final Response
```

---

## Evaluation

### Retrieval

- Recall@K
- Precision@K
- MRR
- NDCG

### Citation

- citation correctness
- citation completeness
- source authority
- exact-section accuracy

### Temporal

- current-version accuracy
- historical-version accuracy
- amendment resolution accuracy

### Safety

- unsupported claim rate
- abstention precision
- conflict detection accuracy

---

## Implementation Priority

### MVP

```text
Authoritative sources
 ↓
Parser
 ↓
Metadata
 ↓
Chunking
 ↓
Vector + BM25
 ↓
Reranker
 ↓
Citation-ready evidence
```

### Next

```text
Version tracking
+
Conflict detection
+
Historical retrieval
+
Multilingual legal retrieval
```

### Advanced

```text
Knowledge graph
+
Rule engine integration
+
Citation verification
+
Agentic orchestration
```

---

## Design Principle

```text
RAG-1
= domain understanding

RAG-2
= authoritative evidence

Rule Engine
= deterministic applicability

LLM
= explanation / language generation

Citation Validator
= verification
```

The backend should never collapse these responsibilities into a single LLM call.
