@echo off
echo ╔════════════════════════════════════════╗
echo ║                                        ║
echo ║            🚀 PassAI 🧠                ║
echo ║    AI-Powered Development Assistant    ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate venv and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking dependencies...
pip install -q -r requirements.txt
echo.

echo Starting Backend and Frontend...
echo.

REM Start backend in new window (with venv activated)
start "PassAI Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && cd backend && python server.py"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak > nul

REM Start frontend in new window
start "PassAI Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ✅ Both services started!
echo Backend: http://localhost:8000
echo Frontend: Electron window
echo.
echo Press any key to exit this window...
pause > nul
