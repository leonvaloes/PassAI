@echo off
echo ========================================
echo   AI Copilot - Reinicio Limpo
echo ========================================
echo.

echo [1/4] Parando processos antigos...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM electron.exe 2>nul
timeout /t 2 >nul

echo [2/4] Iniciando Backend...
start "AI Copilot Backend" cmd /k "cd /d %~dp0 && venv\Scripts\python.exe backend\server.py"
timeout /t 5 >nul

echo [3/4] Iniciando Frontend...
start "AI Copilot Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo [4/4] Pronto!
echo.
echo Backend: http://localhost:8000
echo Frontend: Electron abrindo...
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
