Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "launch_windows.log"
$AppLaunchLogFile = Join-Path $LogDir "launch_windows_app_stderr.log"
$LaunchPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LaunchPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$EntryPoint = Join-Path $ProjectRoot "run_gui.py"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-Utf8BomFile([string]$Path, [string]$Content) {
    $utf8Bom = [System.Text.UTF8Encoding]::new($true)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8Bom)
}

function Write-Log([string]$Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Fail-And-Exit([string]$Message, [int]$Code = 1) {
    Write-Log $Message
    throw $Message
}

Write-Utf8BomFile -Path $LogFile -Content ""
Write-Utf8BomFile -Path $AppLaunchLogFile -Content ""
Write-Log "=== Lancement MotifWorkBench ==="

if (-not (Test-Path -LiteralPath $EntryPoint)) {
    Fail-And-Exit "Fichier introuvable : $EntryPoint"
}

if (-not (Test-Path -LiteralPath $LaunchPython) -and -not (Test-Path -LiteralPath $LaunchPythonw)) {
    Fail-And-Exit "Environnement virtuel introuvable. Lancez d'abord install_and_run_windows.bat."
}

$PythonToUse = $LaunchPython
if (Test-Path -LiteralPath $LaunchPythonw) {
    $PythonToUse = $LaunchPythonw
}

Write-Log "Python utilisé : $PythonToUse"
Write-Log "Point d'entrée : $EntryPoint"

try {
    $process = Start-Process `
        -FilePath $PythonToUse `
        -ArgumentList @($EntryPoint) `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardError $AppLaunchLogFile `
        -PassThru

    Start-Sleep -Seconds 2

    if ($null -ne $process -and $process.HasExited) {
        $details = ""
        if (Test-Path -LiteralPath $AppLaunchLogFile) {
            $details = (Get-Content -LiteralPath $AppLaunchLogFile -Raw -ErrorAction SilentlyContinue).Trim()
        }
        if (-not $details) {
            $details = "L'application s'est fermée immédiatement avec le code $($process.ExitCode)."
        }
        Fail-And-Exit "Échec du lancement. Détails : $details"
    }

    Write-Log "Application lancée avec succès."
    exit 0
}
catch {
    Write-Log "Erreur : $($_.Exception.Message)"
    exit 1
}