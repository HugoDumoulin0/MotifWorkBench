@echo off
setlocal

cd /d "%~dp0"
chcp 65001 >nul

powershell -ExecutionPolicy Bypass -File "%~dp0install_and_run_windows.ps1"
set "EXITCODE=%errorlevel%"

if not "%EXITCODE%"=="0" (
    echo.
    echo [ERREUR] L'installation Windows s'est terminee avec le code %EXITCODE%.
    echo Consultez aussi le journal : logs\install_and_run_windows.log
    pause
)

exit /b %EXITCODE%
