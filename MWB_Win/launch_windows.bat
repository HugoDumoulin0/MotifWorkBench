@echo off
setlocal

cd /d "%~dp0"
chcp 65001 >nul

powershell -ExecutionPolicy Bypass -File "%~dp0launch_windows.ps1"
set "EXITCODE=%errorlevel%"

if not "%EXITCODE%"=="0" (
    echo.
    echo [ERREUR] Le lancement de MotifWorkBench a echoue avec le code %EXITCODE%.
    echo Consultez aussi le journal : logs\launch_windows.log
    pause
)

exit /b %EXITCODE%
