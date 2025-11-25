@echo off
:: Personal Freedom - Optional AI Features Installer
:: Installs GPU-accelerated AI dependencies

echo.
echo =============================================
echo   Personal Freedom - AI Features Installer
echo =============================================
echo.
echo This will install optional AI features:
echo   - Sentiment analysis on session notes
echo   - Distraction trigger detection
echo   - Intelligent break suggestions
echo   - Focus quality trend tracking
echo.
echo Requirements:
echo   - Python 3.8 or higher
echo   - ~800MB download (CPU) or ~2GB (GPU)
echo   - NVIDIA GPU optional (for 5x faster processing)
echo.
echo The app works WITHOUT these features, but they're awesome!
echo.

choice /C YN /M "Do you want to install AI features?"
if errorlevel 2 goto skip
if errorlevel 1 goto install

:install
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo.

:: Detect NVIDIA GPU
echo Detecting GPU...
python -c "import subprocess; subprocess.run(['nvidia-smi'], capture_output=True)" >nul 2>&1
if %errorlevel% equ 0 (
    echo [DETECTED] NVIDIA GPU found!
    echo.
    choice /C YN /M "Install GPU-accelerated version (2GB, 5x faster)?"
    if errorlevel 2 goto cpu_install
    if errorlevel 1 goto gpu_install
) else (
    echo [INFO] No NVIDIA GPU detected, installing CPU version
    goto cpu_install
)

:gpu_install
echo.
echo =============================================
echo   Installing GPU-Accelerated AI (CUDA)
echo =============================================
echo.
echo This will download ~2GB. It may take 5-10 minutes...
echo.

:: Install PyTorch with CUDA
echo [1/2] Installing PyTorch with CUDA 11.8...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyTorch with CUDA
    echo Falling back to CPU version...
    goto cpu_install
)

echo.
echo [2/2] Installing AI models...
pip install transformers sentence-transformers scikit-learn

goto success

:cpu_install
echo.
echo =============================================
echo   Installing CPU-Only AI
echo =============================================
echo.
echo This will download ~800MB. It may take 3-5 minutes...
echo.

pip install -r requirements_ai.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed!
    echo.
    echo Try manual installation:
    echo   pip install torch transformers sentence-transformers scikit-learn
    echo.
    pause
    exit /b 1
)

:success
echo.
echo =============================================
echo   Installation Complete!
echo =============================================
echo.
echo AI Features Installed:
echo   [x] Sentiment Analysis (DistilBERT)
echo   [x] Distraction Detection (MiniLM)
echo   [x] Smart Recommendations
echo.
echo Testing installation...
python -c "import torch; import transformers; import sentence_transformers; print('✓ All AI modules loaded successfully!')"

if %errorlevel% equ 0 (
    echo.
    python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
    echo.
    echo You're all set! Start PersonalFreedom.exe to use AI features.
    echo.
    echo FIRST RUN: AI models will download automatically (~400MB)
    echo This happens once and takes 2-3 minutes.
) else (
    echo.
    echo [WARNING] Installation completed but testing failed
    echo AI features may not work properly
    echo.
)

pause
exit /b 0

:skip
echo.
echo Installation skipped.
echo.
echo You can install AI features later by running:
echo   install_ai.bat
echo.
echo Or manually:
echo   pip install -r requirements_ai.txt
echo.
pause
exit /b 0
