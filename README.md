# 🌿 SIH-Project: IP-SAKTI Full-Stack Platform

An AI-powered intelligence platform uniting **Ayurveda & Traditional Knowledge** with **Authoritative Intellectual Property & Statutory Law**.

---

## 📁 Repository Structure

```
SIH-Project/
├── backend/                       # FastAPI + Multi-RAG Orchestrator
│   ├── app/                       # Microservices, RAG 1, RAG 2, and Orchestrator
│   ├── tests/                     # Unit, integration & contract tests
│   ├── agent.md                   # Authoritative AI Generation Specification
│   ├── vector.db                  # RAG 1 Vector Database
│   ├── vector_rag2.db             # RAG 2 Statutory Vector Database (2,527 chunks)
│   ├── .env                       # Backend Environment & Groq API configuration
│   └── run.py                     # Standalone FastAPI Entrypoint
├── frontend/                      # React 19 + Vite + TailwindCSS Chat Application
│   ├── src/                       # UI components, pages (Landing, Chat), hooks
│   ├── dist/                      # Pre-built production bundle
│   ├── tests/                     # Client contract & interaction tests
│   ├── .env                       # Frontend proxy target (http://127.0.0.1:8000)
│   └── package.json               # Frontend dependencies & scripts
├── package.json                   # Root Full-Stack Gateway
├── run-dev.js                     # Unified concurrent runner
├── start.sh                       # Quick bash launch script
└── README.md                      # Platform overview and instructions
```

---

## 🚀 How to Run the Website

### Method 1: Single-Command Gateway (Recommended)
Simply navigate to the project root and run:
```bash
cd SIH-Project
npm run dev
```
> This starts both:
> - **Backend API** at `http://127.0.0.1:8000` (Swagger docs at `/docs`)
> - **Frontend UI** at `http://localhost:5173` (with hot-reload and automatic `/api` proxy)
> 
> Press **Ctrl+C** to cleanly shut down both servers.

### Alternative: Bash Script
```bash
./start.sh
```

---

## 🧪 Testing

Run both test suites with one command:
```bash
npm test
```
Or individually:
- **Backend Tests** (pytest): `npm run test:backend`
- **Frontend Tests** (contracts + React interactions): `npm run test:frontend`

---

## 🏗️ Production Build & Standalone Mode

To build the frontend and serve everything through FastAPI on a single port (8000):
```bash
npm run build
cd backend && python3 run.py
```
Then open `http://127.0.0.1:8000` in any browser.

## Multilingual, citations, confidence & human review

IP-SAKTI supports a multilingual response selector for major Indian languages. When BHASHINI credentials are configured, the backend translates non-English input to English for the English-heavy RAG corpus and translates the generated answer back to the selected language. BHASHINI uses a pipeline-config call followed by a pipeline-compute call, matching the official ULCA/BHASHINI integration flow.

Configure `BHASHINI_USER_ID`, `BHASHINI_API_KEY`, and `BHASHINI_PIPELINE_ID` in `backend/.env`. Keep credentials server-side; never place them in the frontend. Without BHASHINI credentials, the LLM still responds in the requested language where supported.

Every retrieved source is assigned a deterministic `[S1]`, `[S2]`, ... marker. The answer includes a Sources section, while the UI exposes clickable source cards when a public URL is available.

Each answer receives a confidence score derived from routing confidence and retrieval evidence quality. Low-confidence answers and legal answers below the higher confidence threshold expose a human IP facilitator escalation path. Submissions are persisted to `backend/data/escalations.jsonl`; set `IP_FACILITATOR_EMAIL` to show the configured facilitator contact in the UI.

## Complete frontend integration

See [frontend/README.md](frontend/README.md) for the Research tools panel, answer settings, voice setup, human review, API configuration and verification instructions.

On Windows or Unix, prepare the backend environment with `python -m venv backend/.venv` and `node run-python.js -m pip install -r requirements-dev.txt`. Then use `npm run dev`; `npm test` includes both unittest-style and pytest-style backend tests.

## Deploy to Render

This repository deploys as one Render Docker web service. The root `render.yaml` is the Blueprint and the root `Dockerfile` builds the React bundle and runs FastAPI; keep `frontend/` and `backend/` at the repository root.

1. Push the repository to GitHub or GitLab, then create a Render **Blueprint** from that repository. Render will read `render.yaml` from the root.
2. Use the generated `ip-sakti` web service. Render builds the root multi-stage `Dockerfile`: the first stage compiles React, and the second installs `backend/requirements.txt`, builds both vector databases, and runs FastAPI on Render's `$PORT`.
3. Enter `GROQ_API_KEY` as a secret. Enter `DEEPGRAM_API_KEY` only if Deepgram fallback transcription is needed. To enable BHASHINI, set `BHASHINI_ENABLED=true` and provide the three BHASHINI secrets (`BHASHINI_USER_ID`, `BHASHINI_API_KEY`, and `BHASHINI_PIPELINE_ID`). Never put these values in `frontend/.env`.
4. Keep `USE_LOCAL_RAG2=true` and `ENABLE_MOCK_RAG2=false` for the bundled legal corpus. Set `RAG2_HTTP_URL` only when connecting a separate compatible RAG 2 service.
5. The Blueprint attaches a 1 GB persistent disk at `/var/data` and stores human-review cases at `/var/data/escalations.jsonl`. This requires a paid Render web-service plan; Render service files are otherwise ephemeral. If you deliberately deploy on a free plan, remove the `disk` block and `ESCALATION_STORE_PATH` from `render.yaml`, understanding that review cases will be lost on restart.
6. Wait for the health check at `/api/v1/rag/knowledge/health` to pass, then open `https://<your-service>.onrender.com/chat`. `/`, `/chat`, `/assets/*`, `/animations/*`, and all `/api/*` routes are served by the same service.

The service is intentionally a single web service because FastAPI serves the production React bundle. A separate Render Static Site would need a separate public API origin and CORS/Vite configuration.
