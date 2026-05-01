#!/bin/bash
# Smart Expense Analyzer — single-command launcher.
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "Starting Smart Expense Analyzer..."

# --- Backend ---
echo "[backend] installing dependencies..."
cd "$ROOT/backend"
pip install -r requirements.txt -q
echo "[backend] seeding database..."
python seed.py
echo "[backend] launching API on http://localhost:8000"
python -m uvicorn main:app --reload --port 8000 &
BACK_PID=$!

# --- Frontend ---
echo "[frontend] installing dependencies..."
cd "$ROOT/frontend"
npm install --silent
echo "[frontend] launching dev server on http://localhost:5173"
npm run dev -- --port 5173 &
FRONT_PID=$!

trap "echo 'Shutting down...'; kill $BACK_PID $FRONT_PID 2>/dev/null" INT TERM

echo "----------------------------------------"
echo "Backend:  http://localhost:8000  (docs at /docs)"
echo "Frontend: http://localhost:5173"
echo "----------------------------------------"
wait
