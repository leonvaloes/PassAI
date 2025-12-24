@echo off
REM Automatic CUDA installation - No user input required

echo ========================================
echo Installing PyTorch with CUDA 11.8
echo ========================================
echo.

echo Uninstalling CPU-only PyTorch...
venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio

echo.
echo Installing PyTorch with CUDA 11.8...
echo (This will download ~2.5GB)
echo.

venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo ========================================
echo Verifying installation...
echo ========================================
echo.

venv\Scripts\python.exe -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ Installation complete!
    echo.
    echo Run: venv\Scripts\python.exe src\main.py
) else (
    echo ❌ Error during installation
)
echo.
pause
