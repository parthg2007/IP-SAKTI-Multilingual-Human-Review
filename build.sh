#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "=== Installing frontend dependencies ==="
cd frontend
npm ci --prefer-offline
npm run build
cd "$ROOT_DIR"

echo "=== Copying frontend build into backend bundle ==="
mkdir -p backend/frontend/dist
cp -r frontend/dist/. backend/frontend/dist/

echo "=== Installing Python dependencies ==="
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "=== Building vector databases ==="
python build_vector_db.py
echo "=== Build complete ==="
