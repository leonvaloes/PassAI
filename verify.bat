@echo off
REM Component verification script
echo ========================================
echo AI Copilot - Component Verification
echo ========================================
echo.

venv\Scripts\python.exe -c "import sys; packages = ['whisper', 'torch', 'openai', 'PyQt6', 'cv2', 'sounddevice', 'yaml', 'pydantic', 'mss']; print('Checking components...\n'); [print(f'✅ {p:15} OK') if __import__(p) else print(f'❌ {p:15} FAILED') for p in packages]; print('\n✅ All components verified!')"

echo.
echo ========================================
pause
