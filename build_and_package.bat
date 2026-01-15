@echo off
:: Automated build and installer generation for Personal Liberty
:: Runs the entire process without user interaction

echo.
echo =============================================
echo   Personal Liberty - Automated Build
echo =============================================
echo.

:: Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    exit /b 1
)

:: Check PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Light build - exclude heavy AI libraries
set "HIDDEN_IMPORTS=--hidden-import=productivity_ai --hidden-import=numpy"
set "EXCLUDES=--exclude-module=torch --exclude-module=transformers --exclude-module=sentence_transformers"
set "EXCLUDES=%EXCLUDES% --exclude-module=huggingface_hub --exclude-module=tokenizers"
set "EXCLUDES=%EXCLUDES% --exclude-module=torchaudio --exclude-module=torchvision --exclude-module=cupy --exclude-module=triton"

echo.
echo [Step 1/3] Building executable...
pyinstaller --onefile --windowed --name "PersonalLiberty" ^
    --icon=icons\app.ico ^
    --add-data "productivity_ai.py;." ^
    --add-data "gamification.py;." ^
    %HIDDEN_IMPORTS% ^
    %EXCLUDES% ^
    focus_blocker_qt.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    exit /b 1
)

echo.
echo [Step 2/3] Creating distribution package...
if not exist "dist\PersonalLiberty_Package" mkdir "dist\PersonalLiberty_Package"
copy "dist\PersonalLiberty.exe" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "README.md" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "QUICK_START.md" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "run_as_admin.bat" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "setup_autostart.bat" "dist\PersonalLiberty_Package\" >nul 2>&1
copy "setup_no_uac.bat" "dist\PersonalLiberty_Package\" >nul 2>&1

:: Check if Inno Setup is installed
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo.
    echo [WARNING] Inno Setup not found - skipping installer creation
    echo Install from: https://jrsoftware.org/isinfo.php
    echo.
    echo Build completed successfully!
    echo Executable available at: dist\PersonalLiberty.exe
    exit /b 0
)

echo.
echo [Step 3/3] Creating installer with Inno Setup...

:: Create installer output directory
if not exist "installer_output" mkdir "installer_output"

:: Compile the installer (non-interactive)
"%ISCC%" "installer.iss"

if %errorlevel% neq 0 (
    echo [ERROR] Installer compilation failed!
    exit /b 1
)

echo.
echo =============================================
echo   Build Complete!
echo =============================================
echo.
echo Executable: dist\PersonalLiberty.exe
for %%F in (installer_output\PersonalLiberty_Setup_v*.exe) do echo Installer: %%F
echo.
