@echo off
REM Install PyTorch with CUDA 11.8 support (most stable)

echo ========================================
echo Installing PyTorch with CUDA 11.8
echo ========================================
echo.

echo GPU: RTX 4070 Super
echo Installing PyTorch + CUDA...
echo (This will download ~2GB)
echo.

REM Install PyTorch with CUDA 11.8 (stable)
venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo ========================================
echo Verifying CUDA...
echo ========================================
echo.

venv\Scripts\python.exe -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if hasattr(torch.version, 'cuda') else 'N/A'); print('GPU count:', torch.cuda.device_count() if torch.cuda.is_available() else 0)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ SUCCESS! CUDA is ready!
    echo ========================================
    echo.
    echo Your RTX 4070 Super is now active!
    echo Run: venv\Scripts\python.exe src\main.py
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ Error - CUDA not available
    echo ========================================
    echo.
)

pause
