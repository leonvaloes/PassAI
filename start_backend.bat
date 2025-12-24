@echo off
REM Start Backend API Server

echo Starting AI Copilot Backend...
echo.

REM Stay in root directory, run backend/server.py
venv\Scripts\python.exe backend\server.py

pause
