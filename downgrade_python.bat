@echo off
REM Downgrade to Python 3.11 - Auto-detect version

echo ========================================
echo Python 3.11 + CUDA Setup (Auto-detect)
echo ========================================
echo.

echo Detecting Python 3.11...
echo.

REM Try different Python commands
set PYTHON_CMD=

REM Check python3.11
where python3.11 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3.11
    goto :found
)

REM Check python (default)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo Found: !PYTHON_VER!
    echo !PYTHON_VER! | findstr /C:"3.11" >nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python
        goto :found
    )
)

REM Check py launcher
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.11 --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py -3.11
        goto :found
    )
)

echo ❌ Python 3.11 not found!
echo.
echo Please ensure Python 3.11 is in PATH
pause
exit /b 1

:found
echo ✅ Found Python 3.11: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

pause

echo.
echo Removing old venv...
if exist venv rmdir /s /q venv
echo ✅ Old venv removed
echo.

echo Creating new venv...
%PYTHON_CMD% -m venv venv
echo ✅ Venv created
echo.

echo Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
echo.

echo Installing PyTorch with CUDA 11.8...
venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
echo.

echo Verifying CUDA...
venv\Scripts\python.exe -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
echo.

echo ========================================
echo ✅ Setup Complete!
echo ========================================
pause
