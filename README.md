# IP-SAKTI Sahayak

> **Where Traditional Knowledge Meets Its Rightful Protection**

IP-SAKTI Sahayak is a multilingual, Retrieval-Augmented Generation (RAG)-based AI assistant that helps users explore Ayurveda, traditional-knowledge, intellectual-property, and regulatory questions using source-cited evidence. It is designed to provide traceable, jurisdiction-aware information rather than unsupported chatbot responses.

## Project Information

| Field | Details |
| --- | --- |
| Problem Statement ID | SIH26045 |
| Problem Statement | IP-SAKTI Sahayak - a multilingual, RAG-based, source-cited AI assistant |
| Theme | MedTech / BioTech / HealthTech |
| Category | Software |
| Team | Hallucinators |

## Problem Statement

Ayurvedic practitioners, researchers, startups, and traditional-knowledge holders often need to navigate complex intellectual-property and regulatory requirements. Relevant information is distributed across statutes, treaties, registry records, and traditional-knowledge sources. A general-purpose chatbot can conflate jurisdictions, generate unverifiable statements, or omit the legal sources needed for review.

## Proposed Solution

IP-SAKTI Sahayak provides a multilingual research interface that classifies each query and retrieves evidence from the appropriate knowledge sources before generating a structured, citation-bound response. It separates Indian and international legal contexts, ranks evidence by authority, shows sources, and can route low-confidence cases for human IP-facilitator review.

> **Important:** IP-SAKTI Sahayak is an information and research-support tool. Its responses are not legal advice. Users should consult a qualified professional for decisions involving legal rights, filings, or regulatory compliance.

## Key Features

- Multilingual query and answer support, with optional BHASHINI translation integration
- Dual-RAG retrieval for Ayurveda/traditional-knowledge content and legal/regulatory evidence
- Query routing for conceptual, legal, and hybrid questions
- India and international jurisdiction selection to avoid cross-jurisdiction conflation
- Source-cited answers with deterministic source markers and clickable source cards when public links are available
- Citation ranking, evidence deduplication, conflict detection, and corpus versioning
- Confidence scoring and human IP-facilitator escalation for low-confidence responses
- Research tools for IP classification and Access and Benefit Sharing (ABS) support
- Saved workspace and chat history
- Optional voice interaction support

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 19, Vite, Tailwind CSS, JavaScript |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Retrieval and ML | Dual RAG, scikit-learn, NumPy, hybrid BM25/vector retrieval |
| Data | SQLite-backed vector/chunk stores, JSONL/CSV evidence corpus |
| AI and language services | Groq LLM, optional BHASHINI translation, optional Deepgram transcription |
| Testing | pytest plus frontend contract and interaction tests |
| Deployment | Docker and Render |

## Architecture

```text
User
  |
  v
React + Vite multilingual interface
  |
  v
FastAPI API Gateway
  |
  v
Orchestrator Service
  |
  +--> Query Router (conceptual / legal / hybrid)
  |       |
  |       +--> RAG 1: Ayurveda and traditional-knowledge retrieval
  |       |
  |       +--> RAG 2: Legal and regulatory evidence retrieval
  |
  +--> Citation ranking, conflict detection, and evidence fusion
  |
  v
Groq LLM guardrailed synthesis
  |
  v
Source-cited response + confidence score + optional human escalation
```

The application keeps the RAG 1 and RAG 2 stores separate (`vector.db` and `vector_rag2.db`). The legal corpus preserves source metadata and is versioned to support traceability.

## Repository Structure

```text
YOUR-SIH-PROJECT/
├── README.md                       # Project overview and setup instructions
├── SUBMISSION_GUIDE.md             # SIH submission checklist
├── submission/
│   ├── PRESENTATION.md              # Final presentation or accessible viewer link
│   └── DEMO.md                      # Demo video link and walkthrough
├── src/
  │---IP-SAKTI-Multilingual-Human-Review/
      ├── backend/
      │   ├── app/
      │   │   ├── main.py                 # FastAPI application
      │   │   ├── orchestrator/           # Routing, synthesis, human-review and voice flows
      │   │   ├── rag2/                   # Legal/regulatory RAG, versioning and conflict detection
      │   │   └── data/                   # Data models, storage and ingestion
      │   ├── frontend/                   # React + Vite client application
      │   ├── tests/                      # Backend, integration and contract tests
      │   ├── requirements.txt
      │   └── run.py
      ├── frontend/                       # Root frontend configuration/build assets
      ├── Dockerfile
      ├── render.yaml
      ├── run-dev.js                      # Unified development runner
      ├── start.sh
      └── package.json                      # All project source code starts here
  ├── docs/
  │   └── architecture.md              # Technical architecture documentation
  ├── assets/
  │   └── screenshots/
  │       └── README.md                # Screenshot naming and upload guidance
  ├── requirements.txt                 # Python dependencies
  ├── .gitignore                       # Ignored files and secrets
  └── LICENSE
```

> Keep all application code under `src/`. Do not place source code in `docs/`, `assets/`, `submission/`, or the repository root. If the project grows, create subfolders inside `src/`, such as `src/rag/`, `src/services/`, `src/models/`, and `src/utils/`.

## Getting Started

### Prerequisites

- Python 3.10 or later
- A Groq API key for LLM-powered synthesis

### Install and run locally

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_FOLDER>
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file and add required server-side settings:

```env
GROQ_API_KEY=your_groq_api_key
```

Run the application:

```bash
uvicorn src.main:app --reload
```

Then open:

- API documentation: `http://127.0.0.1:8000/docs`
- Application: `http://127.0.0.1:8000`

### Optional integrations

To enable BHASHINI translation, configure the following values in `.env`:

```env
BHASHINI_ENABLED=true
BHASHINI_USER_ID=your_user_id
BHASHINI_API_KEY=your_api_key
BHASHINI_PIPELINE_ID=your_pipeline_id
```

Use `IP_FACILITATOR_EMAIL` to display the contact for human-review escalation. Configure `DEEPGRAM_API_KEY` only when Deepgram transcription fallback is required.

Never commit `.env` files, API keys, tokens, or other credentials.

## Testing

Run the project's test suite after adding tests under `src/` or a `tests/` directory:

```bash
pytest
```

## Production Build and Deployment

Build a production-ready container or deploy the FastAPI application to the selected cloud provider. Keep Docker, cloud configuration, and deployment documentation outside `src/`; the application code itself remains under `src/`.

Store every API key as a deployment secret, never in the repository.

## Evidence Sources

The project is designed around curated traditional-knowledge, IP, and regulatory evidence, including:

- The Patents Act, 1970 and Patent Rules (India Code)
- The Biological Diversity Act, 2002 and National Biodiversity Authority guidance
- Traditional Knowledge Digital Library (TKDL) and CSIR prior-art material
- Drugs and Cosmetics Act, 1940 and AYUSH licensing rules
- FSSAI Ayurveda Aahara Regulations
- WIPO materials on intellectual property, genetic resources, and associated traditional knowledge

## Impact and Benefits

IP-SAKTI Sahayak aims to make trustworthy IP and regulatory information more accessible for Ayurvedic vaidyas, traditional healers, AYUSH researchers, startups, IP professionals, regulators, and indigenous communities. By grounding answers in cited evidence and separating jurisdictions, it supports more informed research while helping reduce the risk of misinformation and biopiracy.

## Future Scope

- Expand multilingual and voice coverage with language-specific legal terminology validation
- Add knowledge-graph and agentic-reasoning capabilities
- Introduce scheduled, human-curated legal-corpus updates
- Integrate permission-based connectors for paid registry sources
- Extend patent surveillance and prior-art research workflows
- Enhance human-review workflows and institutional dashboards

## Security and Responsible Use

- Do not commit passwords, access tokens, API keys, or `.env` files.
- Keep third-party credentials server-side; never expose them in the frontend.
- Use official and authoritative sources wherever possible.
- Treat generated content as research assistance and verify it before legal, regulatory, or commercial action.

## License

This project is distributed under the license included in the repository. See [LICENSE](LICENSE) for details.
