@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=py -3"
)

if not defined PY_CMD (
    if defined MWB_RUNTIME_ROOT (
        if exist "%MWB_RUNTIME_ROOT%\python\python.exe" (
            set "PY_CMD=%MWB_RUNTIME_ROOT%\python\python.exe"
        )
    )
)

if not defined PY_CMD (
    if exist "%~dp0runtime\python\python.exe" (
        set "PY_CMD=%~dp0runtime\python\python.exe"
    )
)

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo [ERREUR] Aucun Python utilisable trouve.
    echo Installez Python 3.10 a 3.14 ou utilisez MotifWorkBench-Prerequis.exe
    pause
    exit /b 1
)

echo ============================================================
echo MotifWorkBench - Installation rapide et lancement
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creation de l'environnement virtuel...
    call %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Environnement virtuel deja present.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel.
    pause
    exit /b 1
)

echo.
echo Choisissez la variante Torch a installer :
echo   [1] CPU
echo   [2] GPU NVIDIA ^(CUDA 12.6^)
echo.
set /p TORCH_CHOICE="Votre choix [1/2] : "

if "%TORCH_CHOICE%"=="" set "TORCH_CHOICE=1"
if /I "%TORCH_CHOICE%"=="CPU" set "TORCH_CHOICE=1"
if /I "%TORCH_CHOICE%"=="GPU" set "TORCH_CHOICE=2"

if "%TORCH_CHOICE%"=="2" (
    set "TORCH_URL=https://download.pytorch.org/whl/cu126"
    set "TORCH_LABEL=GPU NVIDIA"
) else (
    set "TORCH_URL=https://download.pytorch.org/whl/cpu"
    set "TORCH_LABEL=CPU"
)

echo.
echo [INFO] Mise a jour de pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERREUR] Echec de la mise a jour de pip.
    pause
    exit /b 1
)

echo [INFO] Installation des dependances communes...
python -m pip install -r requirements-windows-common.txt
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances communes.
    pause
    exit /b 1
)

echo [INFO] Installation de Torch (%TORCH_LABEL%)...
python -m pip install torch torchvision --index-url %TORCH_URL%
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation de Torch.
    pause
    exit /b 1
)

echo [INFO] Verification rapide de Torch...
python -c "import torch; print('torch=' + torch.__version__); print('cuda=' + str(torch.cuda.is_available())); print('gpu=' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'))"
if errorlevel 1 (
    echo [ERREUR] Verification Torch echouee.
    pause
    exit /b 1
)

echo.
echo [INFO] Lancement de l'application...
python run_gui.py

echo.
echo [INFO] Le programme s'est termine.
pause
exit /b %errorlevel%
