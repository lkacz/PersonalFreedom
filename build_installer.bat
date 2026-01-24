@echo off
:: Build installer using Inno Setup
:: Requires Inno Setup 6.0+: https://jrsoftware.org/isinfo.php

echo.
echo =============================================
echo   Building Personal Liberty Installer
echo =============================================
echo.

:: Check if Inno Setup is installed
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo [ERROR] Inno Setup not found!
    echo.
    echo Please install Inno Setup 6.0 or later from:
    echo https://jrsoftware.org/isinfo.php
    echo.
    echo Default installation path: C:\Program Files ^(x86^)\Inno Setup 6\
    echo.
    exit /b 1
)

:: Check if executables exist
if not exist "dist\PersonalLiberty.exe" (
    echo [ERROR] PersonalLiberty.exe not found!
    echo Please run build.bat first to create the executables.
    echo.
    exit /b 1
)

:: Create installer output directory
if not exist "installer_output" mkdir "installer_output"

echo Compiling installer with Inno Setup...
echo.

:: Compile the installer
"%ISCC%" "installer.iss"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installer compilation failed!
    exit /b 1
)

echo.
echo =============================================
echo   Installer Build Complete!
echo =============================================
echo.

:: Find the created installer
for %%f in (installer_output\PersonalLiberty_Setup_*.exe) do (
    set "INSTALLER=%%f"
    echo Installer created: %%f
    echo File size: 
    dir "%%f" | findstr /R "[0-9].*PersonalLiberty"
)

echo.
echo DISTRIBUTION:
echo   Location: installer_output\
echo   Ready to distribute!
echo.
echo INSTALLER FEATURES:
echo   - Professional Windows installer
echo   - Start menu shortcuts
echo   - Desktop icon (optional)
echo   - Autostart option
echo   - Clean uninstall with data preservation option
echo.
echo WHAT'S BUNDLED:
echo   - PersonalLiberty.exe (with ALL AI dependencies)
echo   - Complete documentation
echo   - No Python or pip required
echo   - GPU auto-detection
echo.
echo Users just run the installer - everything works immediately!
echo (First launch downloads AI models ~400MB, then fully offline)
echo.
