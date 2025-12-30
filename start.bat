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

REM Start backend in background (same terminal)
cd backend
start /b python server.py
cd ..

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak > nul

REM Start frontend in foreground (blocks terminal - shows Electron output)
cd frontend
call npm start

REM This will only run after npm/electron exits
echo.
echo ✅ Services stopped.
pause
