@echo off
:: Personal Freedom - Setup No-UAC Launch
:: Creates a scheduled task that runs the app with admin privileges without prompting
:: Run this ONCE as administrator to set up the shortcut

echo ============================================
echo  Personal Freedom - No-UAC Setup
echo ============================================
echo.

:: Check if already admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This setup requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

set TASK_NAME=PersonalFreedomLauncher
set APP_PATH=%~dp0dist\PersonalFreedom.exe

:: Check if app exists
if not exist "%APP_PATH%" (
    echo ERROR: PersonalFreedom.exe not found at:
    echo %APP_PATH%
    echo.
    echo Please build the app first using build.bat
    pause
    exit /b 1
)

echo Creating scheduled task for no-UAC launch...
echo App path: %APP_PATH%
echo.

:: Delete existing task if present
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create new task that runs with highest privileges
schtasks /create /tn "%TASK_NAME%" /tr "\"%APP_PATH%\"" /sc onlogon /rl highest /f

if %errorLevel% neq 0 (
    echo.
    echo ERROR: Failed to create scheduled task.
    pause
    exit /b 1
)

echo.
echo SUCCESS! Scheduled task created.
echo.
echo To launch WITHOUT UAC prompt, use:
echo   schtasks /run /tn "%TASK_NAME%"
echo.
echo Creating desktop shortcut...

:: Create a VBS script to make a shortcut that runs the task
set SHORTCUT_VBS=%TEMP%\create_shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SHORTCUT_VBS%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Personal Freedom (No UAC).lnk" >> "%SHORTCUT_VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SHORTCUT_VBS%"
echo oLink.TargetPath = "schtasks" >> "%SHORTCUT_VBS%"
echo oLink.Arguments = "/run /tn %TASK_NAME%" >> "%SHORTCUT_VBS%"
echo oLink.WorkingDirectory = "%~dp0" >> "%SHORTCUT_VBS%"
echo oLink.IconLocation = "%~dp0icons\app.ico" >> "%SHORTCUT_VBS%"
echo oLink.Description = "Personal Freedom - Focus Blocker (No UAC Prompt)" >> "%SHORTCUT_VBS%"
echo oLink.Save >> "%SHORTCUT_VBS%"

cscript //nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"

echo.
echo Desktop shortcut created: "Personal Freedom (No UAC)"
echo.
echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo You can now launch Personal Freedom without UAC prompts
echo using the desktop shortcut or by running:
echo   schtasks /run /tn %TASK_NAME%
echo.
echo To remove this setup, run:
echo   schtasks /delete /tn %TASK_NAME% /f
echo.
pause
