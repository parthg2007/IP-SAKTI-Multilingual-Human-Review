# IP-SAKTI Frontend

React 19 / Vite chat and exploration interface for the IP-SAKTI Multi-RAG backend.

## Quick Start (Unified Full-Stack)

From the main project root (`IP-Sakti- final 3`):
```sh
# Start both Backend (port 8000) and Frontend (port 5173) together
./start.sh
# or
python3 run_dev.py
```

## Running Frontend Standalone

If running the frontend independently:
```sh
npm install
npm run dev
```

The Vite dev server starts on `http://localhost:5173` and proxies all `/api/*` calls to the backend on `http://127.0.0.1:8000` via `.env` (`API_PROXY_TARGET`).

## Testing & Building

```sh
npm test       # Run client integration & contract tests
npm run lint   # Lint codebase
npm run build  # Build production bundle into dist/
```

