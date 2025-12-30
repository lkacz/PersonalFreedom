@echo off
:: Setup autostart for Personal Liberty
:: Adds the app to Windows Startup (runs as admin on login)

echo.
echo =============================================
echo   Personal Liberty - Autostart Setup
echo =============================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%dist\PersonalLibertyTray.exe"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\PersonalLiberty.lnk"
set "TASK_NAME=PersonalLibertyAutostart"

:: Check if exe exists
if not exist "%EXE_PATH%" (
    echo [ERROR] PersonalLibertyTray.exe not found!
    echo Please run build.bat first.
    echo.
    pause
    exit /b 1
)

echo Choose autostart method:
echo.
echo   1. Task Scheduler (Recommended - runs as Admin automatically)
echo   2. Startup Folder (simpler - requires manual admin elevation)
echo   3. Remove autostart
echo   4. Cancel
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto :task_scheduler
if "%choice%"=="2" goto :startup_folder
if "%choice%"=="3" goto :remove_autostart
if "%choice%"=="4" goto :cancel
goto :cancel

:task_scheduler
echo.
echo Creating scheduled task (requires admin)...
echo.

:: Create XML for scheduled task
set "XML_PATH=%TEMP%\pf_task.xml"
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>Personal Liberty Focus Blocker - Autostart^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<LogonTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</LogonTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>%EXE_PATH%^</Command^>
echo       ^<WorkingDirectory^>%SCRIPT_DIR%dist^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XML_PATH%"

:: Import task (requires elevation)
powershell -Command "Start-Process schtasks -ArgumentList '/Create /TN \"%TASK_NAME%\" /XML \"%XML_PATH%\" /F' -Verb RunAs -Wait"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Autostart configured!
    echo Personal Liberty will start automatically with admin rights on login.
) else (
    echo.
    echo [ERROR] Failed to create task. Make sure to allow admin elevation.
)
del "%XML_PATH%" 2>nul
goto :end

:startup_folder
echo.
echo Creating startup shortcut...

:: Create shortcut using PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%SCRIPT_DIR%dist'; $s.Description = 'Personal Liberty Focus Blocker'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo [SUCCESS] Shortcut created in Startup folder!
    echo.
    echo NOTE: You will need to manually accept the admin prompt on each login.
    echo For automatic admin elevation, use option 1 (Task Scheduler).
) else (
    echo.
    echo [ERROR] Failed to create shortcut.
)
goto :end

:remove_autostart
echo.
echo Removing autostart...

:: Remove scheduled task
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    powershell -Command "Start-Process schtasks -ArgumentList '/Delete /TN \"%TASK_NAME%\" /F' -Verb RunAs -Wait"
    echo Removed scheduled task.
)

:: Remove startup shortcut
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo Removed startup shortcut.
)

echo.
echo [SUCCESS] Autostart removed.
goto :end

:cancel
echo.
echo Cancelled.
goto :end

:end
echo.
pause
