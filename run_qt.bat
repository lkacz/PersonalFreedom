@echo off
REM Launch Personal Liberty Qt version without console window
cd /d "%~dp0"
start "" ".venv\\Scripts\\pythonw.exe" "focus_blocker_qt.py"
