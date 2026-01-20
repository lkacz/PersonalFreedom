@echo off
:: Build script for Personal Liberty - Focus Blocker
:: Creates standalone .exe files with all dependencies bundled

echo.
echo =============================================
echo   Building Personal Liberty v6.0.0
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

:: Ensure piper-tts and onnxruntime are installed for TTS bundling
pip show piper-tts >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing piper-tts for voice synthesis...
    pip install piper-tts onnxruntime
)

echo.
echo [1/2] Building with spec file (includes all assets and TTS)...
echo      - Icons and entity graphics
echo      - Voice models for offline TTS  
echo      - Audio synthesis engine
echo      - All game modules
echo.
pyinstaller --clean PersonalLiberty.spec

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Creating distribution package...
if not exist "dist\PersonalLiberty_Package" mkdir "dist\PersonalLiberty_Package"
copy "dist\PersonalLiberty.exe" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "README.md" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "QUICK_START.md" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "run_as_admin.bat" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "setup_autostart.bat" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "setup_no_uac.bat" "dist\PersonalLiberty_Package\" >nul 2>&1

:: Create readme for the package
echo Creating distribution README...
(
echo Personal Liberty v6.0.0 - Gamified Focus Blocker
echo =================================================
echo.
echo QUICK START:
echo 1. Right-click 'run_as_admin.bat' and select "Run as Administrator"
echo 2. OR: Right-click 'PersonalLiberty.exe' ^> Properties ^> Compatibility ^> "Run as administrator"
echo.
echo FEATURES:
echo - Website blocking with timer ^(Full Mode: system-level, Light Mode: notifications^)
echo - Gamification: collect items, level up, unlock achievements
echo - Entity collection with 5 themed storylines
echo - Eye ^& Breath protection with voice guidance
echo - Weight tracking with rewards
echo - Pomodoro timer with breaks
echo.
echo ALL FEATURES ARE FULLY BUNDLED - NO INSTALLATION REQUIRED!
echo - Includes voice synthesis for guided routines ^(offline TTS^)
echo - Includes all game assets ^(icons, entities, sounds^)
echo - Works 100%% offline after installation
echo.
echo NOTES:
echo - Administrator privileges required for website blocking ^(Full Mode^)
echo - Light Mode works without admin privileges
echo.
echo DOCUMENTATION:
echo - README.md - Full feature documentation
echo - QUICK_START.md - Quick reference guide
echo.
echo AUTOSTART:
echo - Run 'setup_autostart.bat' to start with Windows
echo.
echo For more info: https://github.com/lkacz/PersonalLiberty
) > "dist\PersonalLiberty_Package\START_HERE.txt"

echo Done! Package created in: dist\PersonalLiberty_Package\

echo.
echo =============================================
echo   Build Complete! v6.0.0
echo =============================================
echo.
echo DISTRIBUTION PACKAGE: %SCRIPT_DIR%dist\PersonalLiberty_Package\
echo.
echo Contents:
echo   - PersonalLiberty.exe        ^(Fully self-contained^)
echo   - START_HERE.txt             ^(Quick instructions^)
echo   - README.md                  ^(Full documentation^)
echo   - QUICK_START.md             ^(Quick reference^)
echo   - run_as_admin.bat           ^(Admin launcher^)
echo   - setup_autostart.bat        ^(Autostart setup^)
echo.
echo BUNDLED ASSETS:
echo   - Voice models for offline TTS
echo   - Entity graphics ^(45+ SVG files^)
echo   - Sound synthesis engine
echo   - All game modules and dialogs
echo.
echo To distribute: Zip the PersonalLiberty_Package folder
echo.
pause
