@echo off
:: Master build script - Creates both standalone package AND installer
:: Run this to build everything from scratch

echo.
echo =============================================
echo   Personal Liberty - MASTER BUILD
echo =============================================
echo.
echo This will create:
echo   1. Standalone package (PersonalLiberty_Package folder)
echo   2. Windows Installer (PersonalLiberty_Setup.exe)
echo.
echo Both include FULLY BUNDLED AI - no dependencies needed!
echo.
pause

:: Step 1: Build executables with bundled AI
echo.
echo =============================================
echo   STEP 1: Building Executables
echo =============================================
echo.
call build.bat
if %errorlevel% neq 0 (
    echo [ERROR] Executable build failed!
    pause
    exit /b 1
)

:: Step 2: Build installer
echo.
echo =============================================
echo   STEP 2: Building Installer
echo =============================================
echo.
call build_installer.bat
if %errorlevel% neq 0 (
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

:: Summary
echo.
echo =============================================
echo   BUILD COMPLETE - DISTRIBUTION READY!
echo =============================================
echo.
echo TWO DISTRIBUTION OPTIONS CREATED:
echo.
echo 1. PORTABLE VERSION (no install needed):
echo    Location: dist\PersonalLiberty_Package\
echo    Contents: Just extract and run PersonalLiberty.exe
echo    Size: ~500MB (includes all AI libraries)
echo.
echo 2. WINDOWS INSTALLER (professional):
echo    Location: installer_output\PersonalLiberty_Setup_v2.1.exe
echo    Features: Start menu, desktop icon, autostart, uninstaller
echo    Size: ~500MB (single file installer)
echo.
echo WHAT'S BUNDLED IN BOTH:
echo   ✓ PyTorch with CUDA support
echo   ✓ Transformers (DistilBERT, MiniLM, DistilBART)
echo   ✓ Sentence-Transformers
echo   ✓ All productivity AI features
echo   ✓ GPU auto-detection
echo   ✓ Complete documentation
echo.
echo USERS GET:
echo   • Zero dependencies - just run it
echo   • No Python installation needed
echo   • No pip or package management
echo   • First launch: Downloads AI models (~400MB, one-time)
echo   • Then works 100%% offline forever
echo   • Automatic GPU acceleration if available
echo.
echo FILES READY FOR DISTRIBUTION:
echo   - Zip dist\PersonalLiberty_Package\ for portable version
echo   - Upload installer_output\PersonalLiberty_Setup_v2.1.exe
echo.
echo Ready to distribute! 🚀
echo.
pause
