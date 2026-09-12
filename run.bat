@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   The Lenny Growth Assistant - 1-Click Startup Launcher
echo =======================================================
echo.

:: 1. Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Notice: Ollama does not seem to be running on http://localhost:11434.
    echo     Please make sure 'ollama serve' is running in another terminal if using local models.
    echo.
) else (
    echo [✓] Local Ollama service detected.
)

:: 2. Check virtual environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [*] Setting up Python virtual environment...
    python -m venv backend\venv
    call backend\venv\Scripts\pip install -r backend\requirements.txt
)

:: 3. Start Backend in separate window
echo [*] Starting FastAPI Backend on http://localhost:8000 ...
start "Lenny Assistant Backend" cmd /k "backend\venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 4. Start Frontend
echo [*] Starting Frontend UI on http://localhost:3000 ...
cd frontend
if not exist "node_modules" (
    echo [*] Installing frontend npm dependencies...
    call npm install
)
call npm run dev

pause
