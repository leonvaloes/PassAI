@echo off
REM Enable CUDA - Downgrade to Python 3.10 with CUDA support

echo ========================================
echo CUDA GPU Acceleration Setup
echo ========================================
echo.
echo This will:
echo 1. Install Python 3.10 (has CUDA builds)
echo 2. Rebuild venv with Python 3.10
echo 3. Install PyTorch with CUDA 11.8
echo 4. Verify GPU is active
echo.

pause

echo.
echo Step 1: Installing Python 3.10...
echo ========================================
echo.

winget install Python.Python.3.10 --silent

echo.
echo Step 2: Removing old venv...
echo ========================================
echo.

taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul
rmdir /s /q venv

echo.
echo Step 3: Creating venv with Python 3.10...
echo ========================================
echo.

REM Try different commands
py -3.10 -m venv venv
if %ERRORLEVEL% NEQ 0 (
    python3.10 -m venv venv
)
if %ERRORLEVEL% NEQ 0 (
    python -m venv venv
)

echo.
echo Step 4: Installing dependencies...
echo ========================================
echo.

venv\Scripts\python.exe --version
venv\Scripts\python.exe -m pip install --upgrade pip

echo Installing core dependencies...
venv\Scripts\python.exe -m pip install openai-whisper sounddevice opencv-python openai pyyaml pydantic PyQt6 mss psutil requests scikit-learn python-dotenv

echo.
echo Step 5: Installing PyTorch with CUDA 11.8...
echo ========================================
echo (Downloading ~2.5GB)
echo.

venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo Step 6: Verifying CUDA...
echo ========================================
echo.

venv\Scripts\python.exe -c "import torch; print(''); print('✅ CUDA Available:', torch.cuda.is_available()); print('GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'); print('CUDA Version:', torch.version.cuda if hasattr(torch.version, 'cuda') else 'N/A'); print('PyTorch:', torch.__version__)"

echo.
venv\Scripts\python.exe -c "import torch; exit(0 if torch.cuda.is_available() else 1)"
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo ✅ SUCCESS! GPU IS ACTIVE!
    echo ========================================
    echo.
    echo Configure for GPU:
    echo   .\configure_gpu.bat
    echo.
    echo Run:
    echo   venv\Scripts\python.exe src\main.py
    echo.
) else (
    echo ========================================
    echo ⚠️ GPU not active - using CPU
    echo ========================================
    echo.
    echo System will work but without GPU acceleration.
    echo Check CUDA Toolkit is installed.
    echo.
)

pause
