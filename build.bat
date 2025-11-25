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

:: Collect hidden imports for AI models
set "HIDDEN_IMPORTS=--hidden-import=productivity_ai --hidden-import=local_ai --hidden-import=transformers --hidden-import=torch --hidden-import=sentence_transformers --hidden-import=sklearn --hidden-import=sklearn.metrics --hidden-import=sklearn.metrics.pairwise"

echo.
echo [1/3] Building GUI version (with AI)...
pyinstaller --onefile --windowed --name "PersonalFreedom" ^
    --icon=NONE ^
    --add-data "productivity_ai.py;." ^
    --add-data "local_ai.py;." ^
    %HIDDEN_IMPORTS% ^
    focus_blocker.py 2>nul

if %errorlevel% neq 0 (
    echo [RETRY] Building without some hidden imports...
    pyinstaller --onefile --windowed --name "PersonalFreedom" ^
        --add-data "productivity_ai.py;." ^
        --add-data "local_ai.py;." ^
        focus_blocker.py
)

echo.
echo [2/3] Building System Tray version...
pip show pystray >nul 2>&1
if %errorlevel% equ 0 (
    pyinstaller --onefile --windowed --name "PersonalFreedomTray" --icon=NONE tray_blocker.py 2>nul
    if %errorlevel% neq 0 (
        pyinstaller --onefile --windowed --name "PersonalFreedomTray" tray_blocker.py
    )
) else (
    echo [SKIP] pystray not installed, skipping tray version
)

echo.
echo [3/3] Creating distribution package...
if not exist "dist\PersonalFreedom_Package" mkdir "dist\PersonalFreedom_Package"
copy "dist\PersonalFreedom.exe" "dist\PersonalFreedom_Package\" >nul 2>&1
if exist "dist\PersonalFreedomTray.exe" copy "dist\PersonalFreedomTray.exe" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "README.md" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "QUICK_START.md" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "GPU_AI_GUIDE.md" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "requirements_ai.txt" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "run_as_admin.bat" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "setup_autostart.bat" "dist\PersonalFreedom_Package\" >nul 2>&1
copy "install_ai.bat" "dist\PersonalFreedom_Package\" >nul 2>&1

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
echo AI FEATURES:
echo - Basic AI features work out of the box ^(pattern analysis, achievements^)
echo - For GPU-accelerated AI ^(sentiment analysis, distraction detection^):
echo   1. Double-click 'install_ai.bat' ^(auto-detects GPU^)
echo   2. OR: Install Python 3.8+, then: pip install -r requirements_ai.txt
echo   3. Restart the application
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
echo   - PersonalFreedom.exe        ^(Main application with bundled AI^)
echo   - PersonalFreedomTray.exe    ^(System tray version^)
echo   - START_HERE.txt             ^(Quick instructions^)
echo   - README.md                  ^(Full documentation^)
echo   - QUICK_START.md             ^(Quick reference^)
echo   - GPU_AI_GUIDE.md            ^(AI features guide^)
echo   - install_ai.bat             ^(AI installer - auto-detects GPU^)
echo   - requirements_ai.txt        ^(Optional AI dependencies^)
echo   - run_as_admin.bat           ^(Admin launcher^)
echo   - setup_autostart.bat        ^(Autostart setup^)
echo.
echo NOTES:
echo   - Basic AI ^(achievements, stats^) works immediately
echo   - For GPU AI: Double-click install_ai.bat ^(auto-detects GPU^)
echo   - Run as Administrator for website blocking!
echo.
echo To distribute: Zip the PersonalFreedom_Package folder
echo.
pause
