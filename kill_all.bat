@echo off
echo Matando processos do PassAI...

taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM electron.exe /T 2>nul
taskkill /F /IM "PassAI.exe" /T 2>nul

echo.
echo Processos finalizados!
echo Agora voce pode rodar start.bat novamente com seguranca.
pause
