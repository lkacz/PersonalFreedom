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

echo.
echo [1/2] Building GUI version...
pyinstaller --onefile --windowed --name "PersonalFreedom" --icon=NONE --add-data "config.json;." focus_blocker.py 2>nul
if %errorlevel% neq 0 (
    pyinstaller --onefile --windowed --name "PersonalFreedom" focus_blocker.py
)

echo.
echo [2/2] Building System Tray version...
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
echo =============================================
echo   Build Complete!
echo =============================================
echo.
echo Executables are in: %SCRIPT_DIR%dist\
echo.
echo   - PersonalFreedom.exe     (GUI version)
echo   - PersonalFreedomTray.exe (System tray version)
echo.
echo NOTE: Run as Administrator for blocking to work!
echo.
pause
