# IP-SAKTI Frontend

React 19 / Vite interface for the IP-SAKTI backend. The root `frontend/` directory is the maintained frontend; `backend/frontend/dist/` is the deployment fallback bundle.

## Run

From the repository root:

```sh
python -m venv backend/.venv
node run-python.js -m pip install -r requirements-dev.txt
npm install
npm run dev
```

The launcher uses `backend/.venv` when available and works on Windows and Unix. Vite normally uses port 5173 and reports a different port if it is occupied. All `/api` calls proxy to `http://127.0.0.1:8000` by default. Set `API_PROXY_TARGET` in `frontend/.env` for a different backend; set `VITE_API_BASE_URL` only when the browser must call another origin directly (with appropriate backend CORS configuration).

## Features

Open `/chat` and use **Research tools** in the sidebar:

- **Evidence search:** domain and legal search, hybrid/BM25/vector methods, domain/category filters, legal jurisdiction, and up to 50 results.
- **Source query:** direct domain or legal evidence context, selected language and jurisdiction, legal category/domain filters, optional as-of date, and statutory qualifications.
- **Legal history:** date-specific evidence with provision versions and jurisdiction. This endpoint searches across jurisdictions.
- **Routing preview:** backend intent, explanation, confidence and selected sources. Chat routing can change after translation or for international scope.
- **Services:** backend metadata, index health, connected-service health, and external RAG registration. Remote services must implement `/api/v1/rag/query`, `/api/v1/rag/search`, and `/api/v1/rag/health`. Registrations are in memory until the backend restarts.

**Answer settings** controls automatic/explicit source selection and evidence count per source. The chat retains the settings used for each answer and retry. Answer cards expose citation markers, excerpts, source links, legal document details, confidence, responding services, retrieval context, reasoning steps and graph relationships.

The language selector loads `/api/v1/languages`. BHASHINI translation needs `BHASHINI_ENABLED=true` plus its three credentials in `backend/.env`. Other backend translation paths remain available according to backend configuration.

Voice input uses browser-supported audio formats and the backend transcription endpoint. Microphone access requires localhost or HTTPS. Groq Whisper or Deepgram credentials stay in the backend. Browser speech recognition is used where MediaRecorder is unavailable. Recording stops after one minute; navigation releases the microphone and cancels pending transcription. Read-aloud uses the answer language and browser-installed voices.

Human review sends the original question, answer, jurisdiction, language and full citation provenance to `/api/v1/human/escalate`. The backend stores the case in its configured JSONL queue. A case ID is retained in local chat history; this is not an email-delivery or review-status tracking system. The backend accepts up to 100 sources and 64,000 answer characters per case.

## Verification

From the repository root:

```sh
npm test
npm run build
npm --prefix frontend run lint
```

`npm test` runs all backend pytest tests, frontend HTTP contract tests and React interaction tests. The default backend suite disables external LLM/translation providers and uses temporary files for review cases. UI tests mock network responses and microphone APIs; they do not test live audio hardware or provider credentials.

A production build goes to `frontend/dist/`. FastAPI prefers this build over `backend/frontend/dist/`; restart the backend after building to refresh static mount discovery. Render's root multi-stage `Dockerfile` builds this bundle and copies it into the backend image. `build.sh` remains available for native local/Render fallback builds.
