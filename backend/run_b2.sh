#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Developer B2 — One-Command Backend Setup, Test & Run Script
# ==============================================================================

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "🐍 Creating Python virtual environment in backend/.venv..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installing FastAPI & test dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "📝 Creating backend/.env from ../.env.example..."
  cp ../.env.example .env
fi

echo "🧪 Running automated pytest suite..."
PYTHONPATH=. python -m pytest -v

echo "🚀 Starting Candy or Curse FastAPI Backend on http://0.0.0.0:8000 ..."
echo "👉 Interactive Swagger UI: http://localhost:8000/docs"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
