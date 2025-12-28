@echo off
REM Launch Personal Freedom Qt version without console window
cd /d "%~dp0"
start "" ".venv_qt\Scripts\pythonw.exe" "focus_blocker_qt.py"
