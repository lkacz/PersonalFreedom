@echo off
:: Personal Liberty - System Tray Launcher
:: Runs the system tray version with Administrator privileges

echo Starting Personal Liberty in system tray...

set "SCRIPT_DIR=%~dp0"

:: Request admin privileges and run the tray script (hidden)
powershell -Command "Start-Process pythonw -ArgumentList '\"%SCRIPT_DIR%tray_blocker.py\"' -Verb RunAs -WindowStyle Hidden"

exit /b 0
