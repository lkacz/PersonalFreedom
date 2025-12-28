@echo off
:: Quick build script - builds lightweight executables without bundled AI
:: AI features will work if user has packages installed separately

echo.
echo =============================================
echo   Building Personal Freedom (Lightweight)
echo =============================================
echo.

cd /d "%~dp0"

:: Check PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/2] Building Main GUI...
pyinstaller --noconfirm --onefile --windowed --uac-admin ^
    --name "PersonalFreedom" ^
    --add-data "productivity_ai.py;." ^
    --add-data "local_ai.py;." ^
    --hidden-import=productivity_ai ^
    focus_blocker.py

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build main app!
    pause
    exit /b 1
)

echo.
echo [2/2] Building System Tray version...
pyinstaller --noconfirm --onefile --windowed --uac-admin ^
    --name "PersonalFreedomTray" ^
    tray_blocker.py

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build tray app!
    pause
    exit /b 1
)

echo.
echo =============================================
echo   Build Complete!
echo =============================================
echo.
echo Output files:
echo   dist\PersonalFreedom.exe
echo   dist\PersonalFreedomTray.exe
echo.
echo Now run: build_installer.bat
echo.
pause
