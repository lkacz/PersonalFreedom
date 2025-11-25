@echo off
:: Personal Freedom - Focus Blocker Launcher
:: This script runs the application with Administrator privileges

echo.
echo  ===============================================
echo   Personal Freedom - Focus Blocker
echo   Block distracting websites during focus time
echo  ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

:: Request admin privileges and run the main script
echo Requesting administrator privileges...
powershell -Command "Start-Process python -ArgumentList '\"%SCRIPT_DIR%focus_blocker.py\"' -Verb RunAs"

exit /b 0
