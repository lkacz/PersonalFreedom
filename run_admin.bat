@echo off
:: Personal Freedom - Run as Administrator
:: This batch file requests admin privileges and launches the app

:: Check if already admin
net session >nul 2>&1
if %errorLevel% == 0 (
    cd /d "%~dp0"
    python focus_blocker_qt.py
) else (
    :: Request admin elevation
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
)
