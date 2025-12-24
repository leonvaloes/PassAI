@echo off
REM Quick fix - Rebuild venv cleanly

echo ========================================
echo Rebuilding Virtual Environment
echo ========================================
echo.

echo Closing any Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo.
echo Removing old venv...
timeout /t 2 >nul
rmdir /s /q venv

echo.
echo Creating fresh venv with Python 3.11...
py -3.11 -m venv venv

echo.
echo Installing core dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install openai-whisper torch sounddevice opencv-python openai pyyaml pydantic PyQt6 mss psutil requests scikit-learn

echo.
echo Verifying installation...
venv\Scripts\python.exe -c "import whisper, torch, sounddevice, cv2, openai, yaml, pydantic, mss; print('All modules OK')"

echo.
echo ========================================
echo ✅ Setup Complete!
echo ========================================
echo Run: venv\Scripts\python.exe src\main.py
echo.
pause
