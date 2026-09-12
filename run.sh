#!/usr/bin/env bash
set -e

echo "======================================================="
echo "  The Lenny Growth Assistant - 1-Click Startup Launcher"
echo "======================================================="
echo ""

# 1. Check Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[✓] Local Ollama service detected."
else
    echo "[!] Notice: Ollama not detected on http://localhost:11434."
    echo "    Run 'ollama serve' in another terminal if evaluating local models."
fi

# 2. Check Python venv
if [ ! -f "backend/venv/bin/python" ]; then
    echo "[*] Setting up Python virtual environment..."
    python3 -m venv backend/venv
    backend/venv/bin/pip install -r backend/requirements.txt
fi

# 3. Start Backend
echo "[*] Starting FastAPI Backend on http://localhost:8000 ..."
backend/venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

trap "kill $BACKEND_PID" EXIT

# 4. Start Frontend
echo "[*] Starting Frontend UI on http://localhost:3000 ..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev
