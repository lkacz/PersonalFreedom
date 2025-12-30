@echo off
:: Build script for Personal Freedom - Focus Blocker
:: Creates standalone .exe files

echo.
echo =============================================
echo   Building Personal Freedom
echo =============================================
echo.

:: Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Check PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Collect hidden imports for AI models (comprehensive list)
set "HIDDEN_IMPORTS=--hidden-import=productivity_ai --hidden-import=local_ai"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=transformers --hidden-import=transformers.models --hidden-import=transformers.models.distilbert"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=transformers.models.bert --hidden-import=transformers.models.bart"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=torch --hidden-import=torch.nn --hidden-import=torch.cuda"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=sentence_transformers --hidden-import=sentence_transformers.models"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=sklearn --hidden-import=sklearn.metrics --hidden-import=sklearn.metrics.pairwise"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=numpy --hidden-import=scipy"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --hidden-import=tokenizers --hidden-import=huggingface_hub"
set "HIDDEN_IMPORTS=%HIDDEN_IMPORTS% --collect-all=transformers --collect-all=sentence_transformers --collect-all=torch"

echo.
echo [1/2] Building GUI version with FULL AI bundle...
echo (This may take 5-10 minutes - bundling PyTorch and transformers)
pyinstaller --onefile --windowed --name "PersonalFreedom" ^
    --icon=icons\app.ico ^
    --add-data "productivity_ai.py;." ^
    --add-data "local_ai.py;." ^
    --add-data "gamification.py;." ^
    %HIDDEN_IMPORTS% ^
    focus_blocker_qt.py

echo.
echo [2/2] Creating distribution package...
if not exist "dist\PersonalFreedom_Package" mkdir "dist\PersonalFreedom_Package"
copy "dist\PersonalFreedom.exe" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "README.md" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "QUICK_START.md" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "run_as_admin.bat" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "setup_autostart.bat" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "setup_no_uac.bat" "dist\PersonalFreedom_Package\" >nul 2>&1

:: Create readme for the package
echo Creating distribution README...
(
echo Personal Freedom - AI-Powered Focus Blocker
echo ==========================================
echo.
echo QUICK START:
echo 1. Right-click 'run_as_admin.bat' and select "Run as Administrator"
echo 2. OR: Right-click 'PersonalFreedom.exe' ^> Properties ^> Compatibility ^> "Run as administrator"
echo.
echo FEATURES:
echo - Website blocking with timer
echo - Category management
echo - Scheduled blocking
echo - Statistics and productivity insights
echo - AI-powered achievements and goal tracking
echo - GPU-accelerated sentiment analysis ^(if GPU available^)
echo - Distraction pattern detection
echo - Smart break suggestions
echo.
echo ALL AI FEATURES ARE FULLY BUNDLED - NO INSTALLATION REQUIRED!
echo The app will automatically detect GPU and use it if available.
echo.
echo NOTES:
echo - Administrator privileges required for website blocking
echo - First launch may be slow ^(~30 seconds^) while AI models download
echo - Models are cached locally ^(~400MB in AppData^)
echo - 100%% private - all AI runs locally, no internet required after setup
echo.
echo DOCUMENTATION:
echo - README.md - Full feature documentation
echo - QUICK_START.md - Quick reference guide
echo - GPU_AI_GUIDE.md - GPU AI installation and usage
echo.
echo AUTOSTART:
echo - Run 'setup_autostart.bat' to start with Windows
echo.
echo NOTE: Administrator privileges required for website blocking to work!
echo.
echo For more info: https://github.com/lkacz/PersonalFreedom
) > "dist\PersonalFreedom_Package\START_HERE.txt"

echo Done! Package created in: dist\PersonalFreedom_Package\

echo.
echo =============================================
echo   Build Complete!
echo =============================================
echo.
echo DISTRIBUTION PACKAGE: %SCRIPT_DIR%dist\PersonalFreedom_Package\
echo.
echo Contents:
echo   - PersonalFreedom.exe        ^(Fully self-contained with AI^)
echo   - PersonalFreedomTray.exe    ^(System tray version^)
echo   - START_HERE.txt             ^(Quick instructions^)
echo   - README.md                  ^(Full documentation^)
echo   - QUICK_START.md             ^(Quick reference^)
echo   - run_as_admin.bat           ^(Admin launcher^)
echo   - setup_autostart.bat        ^(Autostart setup^)
echo.
echo NOTES:
echo   - ALL AI features bundled - no installation needed!
echo   - First launch: ~30 sec to download AI models ^(~400MB, one-time^)
echo   - Automatically detects and uses GPU if available
echo   - 100%% private - runs completely offline after initial setup
echo   - Run as Administrator for website blocking!
echo.
echo To distribute: Zip the PersonalFreedom_Package folder
echo.
pause
