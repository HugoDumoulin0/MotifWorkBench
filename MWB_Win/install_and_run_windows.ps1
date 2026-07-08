param(
    [switch]$SkipRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "install_and_run_windows.log"
$LaunchLogFile = Join-Path $LogDir "install_and_run_windows_launch.log"
$RequirementsFile = Join-Path $ProjectRoot "requirements-windows-common.txt"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-Log([string]$Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Find-ExistingFile([string[]]$Candidates) {
    foreach ($candidate in $Candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Find-PythonCommand {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        return @{
            Kind = "py"
            Command = $py.Source
            Display = "$($py.Source) -3"
        }
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        return @{
            Kind = "python"
            Command = $python.Source
            Display = $python.Source
        }
    }

    $path = Find-ExistingFile @(
        "$env:LocalAppData\Programs\Python\Python312\python.exe",
        "$env:LocalAppData\Programs\Python\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python313\python.exe"
    )
    if ($path) {
        return @{
            Kind = "python"
            Command = $path
            Display = $path
        }
    }

    return $null
}

function Find-Rscript {
    $cmd = Get-Command Rscript.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $fixedPath = Find-ExistingFile @(
        "$env:ProgramFiles\R\R-4.5.2\bin\Rscript.exe",
        "$env:ProgramFiles\R\R-4.5.2\bin\x64\Rscript.exe",
        "$env:ProgramFiles\R\R-4.5.1\bin\Rscript.exe",
        "$env:ProgramFiles\R\R-4.5.1\bin\x64\Rscript.exe"
    )
    if ($fixedPath) {
        return $fixedPath
    }

    $searchRoots = @(
        (Join-Path $env:ProgramFiles "R"),
        (Join-Path ${env:ProgramFiles(x86)} "R")
    )

    foreach ($root in $searchRoots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) {
            continue
        }

        $candidate = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object {
                @(
                    (Join-Path $_.FullName "bin\Rscript.exe"),
                    (Join-Path $_.FullName "bin\x64\Rscript.exe")
                )
            } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1

        if ($candidate) {
            return $candidate
        }
    }

    return $null
}

function Find-Perl {
    $cmd = Get-Command perl.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    return Find-ExistingFile @(
        "C:\Strawberry\perl\bin\perl.exe",
        "C:\Strawberry\c\bin\perl.exe",
        "$env:ProgramFiles\Strawberry\perl\bin\perl.exe"
    )
}

function Get-Winget {
    return Get-Command winget.exe -ErrorAction SilentlyContinue
}

function Install-WithWinget([string]$PackageId, [string]$Label) {
    $winget = Get-Winget
    if (-not $winget) {
        throw "winget is not available. Cannot install $Label automatically."
    }

    Write-Log "Automatic install of $Label via winget ($PackageId)..."
    $arguments = @(
        "install",
        "--id", $PackageId,
        "-e",
        "--source", "winget",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity"
    )

    $process = Start-Process -FilePath $winget.Source -ArgumentList $arguments -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -ne 0) {
        throw "winget failed for $Label (code $($process.ExitCode))."
    }
}

function Ensure-Dependency([string]$Name, [scriptblock]$Finder, [string]$WingetId, [string]$ManualHint) {
    $path = & $Finder
    if ($path) {
        Write-Log "$Name already detected: $path"
        return $path
    }

    Write-Log "$Name not detected. Trying automatic install..."
    try {
        Install-WithWinget -PackageId $WingetId -Label $Name
    } catch {
        Write-Log "Automatic install failed for ${Name}: $($_.Exception.Message)"
        throw "$Name was not installed automatically. $ManualHint"
    }

    Start-Sleep -Seconds 3
    $path = & $Finder
    if (-not $path) {
        throw "$Name seems installed but is still not found. $ManualHint"
    }

    Write-Log "$Name installed: $path"
    return $path
}

function Ensure-Python {
    $pythonInfo = Find-PythonCommand
    if ($pythonInfo) {
        Write-Log "Python already detected: $($pythonInfo.Display)"
        return $pythonInfo
    }

    Write-Log "Python not detected. Trying automatic install..."
    try {
        Install-WithWinget -PackageId "Python.Python.3.12" -Label "Python"
    } catch {
        Write-Log "Automatic install failed for Python: $($_.Exception.Message)"
        throw "Python was not installed automatically. Install Python 3.12 with standard options, then run this script again."
    }

    Start-Sleep -Seconds 3
    $pythonInfo = Find-PythonCommand
    if (-not $pythonInfo) {
        throw "Python seems installed but is still not found. Install Python 3.12 with standard options, then run this script again."
    }

    Write-Log "Python installed: $($pythonInfo.Display)"
    return $pythonInfo
}

function Convert-ToProcessArgumentString([string[]]$Arguments) {
    if (-not $Arguments -or $Arguments.Count -eq 0) {
        return ""
    }

    $escaped = foreach ($argument in $Arguments) {
        if ($null -eq $argument) {
            '""'
            continue
        }

        if ($argument -match '[\s"]') {
            '"' + ($argument -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
        } else {
            $argument
        }
    }

    return ($escaped -join " ")
}

function Invoke-LoggedProcess(
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$StepLabel,
    [string]$WorkingDirectory = $ProjectRoot
) {
    Write-Log "Running [$StepLabel]: $FilePath $($Arguments -join ' ')"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = Convert-ToProcessArgumentString -Arguments $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $psi.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    while (-not $process.StandardOutput.EndOfStream) {
        $line = $process.StandardOutput.ReadLine()
        if ($null -ne $line) {
            Write-Log $line
        }
    }

    while (-not $process.StandardError.EndOfStream) {
        $line = $process.StandardError.ReadLine()
        if ($null -ne $line) {
            Write-Log $line
        }
    }

    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "Step failed [$StepLabel] with code $($process.ExitCode)."
    }
}

function Ensure-Venv([hashtable]$PythonInfo) {
    if (Test-Path -LiteralPath $VenvPython) {
        Write-Log "Virtual environment already present: $VenvPython"
        return
    }

    Write-Log "Creating virtual environment..."
    if ($PythonInfo.Kind -eq "py") {
        Invoke-LoggedProcess -FilePath $PythonInfo.Command -Arguments @("-3", "-m", "venv", ".venv") -StepLabel "Create venv"
    } else {
        Invoke-LoggedProcess -FilePath $PythonInfo.Command -Arguments @("-m", "venv", ".venv") -StepLabel "Create venv"
    }
}

function Ask-TorchMode {
    Write-Host ""
    Write-Host "Choose Torch mode to install:"
    Write-Host "  [1] CPU"
    Write-Host "  [2] GPU NVIDIA (CUDA 12.6)"
    Write-Host ""
    $choice = Read-Host "Your choice [1/2]"

    if ([string]::IsNullOrWhiteSpace($choice)) {
        return @{
            Label = "CPU"
            Url = "https://download.pytorch.org/whl/cpu"
        }
    }

    if ($choice -eq "2" -or $choice.ToUpperInvariant() -eq "GPU") {
        return @{
            Label = "GPU NVIDIA"
            Url = "https://download.pytorch.org/whl/cu126"
        }
    }

    return @{
        Label = "CPU"
        Url = "https://download.pytorch.org/whl/cpu"
    }
}

function Install-PythonDependencies([hashtable]$TorchMode) {
    if (-not (Test-Path -LiteralPath $RequirementsFile)) {
        throw "Missing file: $RequirementsFile"
    }

    Invoke-LoggedProcess -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -StepLabel "Upgrade pip"
    Invoke-LoggedProcess -FilePath $VenvPython -Arguments @("-m", "pip", "install", "-r", $RequirementsFile) -StepLabel "Install requirements"
    Invoke-LoggedProcess -FilePath $VenvPython -Arguments @("-m", "pip", "install", "torch", "torchvision", "--index-url", $TorchMode.Url) -StepLabel "Install Torch $($TorchMode.Label)"
    Invoke-LoggedProcess -FilePath $VenvPython -Arguments @("-c", "import torch; print('torch=' + torch.__version__); print('cuda=' + str(torch.cuda.is_available())); print('gpu=' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'))") -StepLabel "Verify Torch"
}

function Launch-Application {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        throw "Virtual environment Python not found: $VenvPython"
    }

    $launchPython = $VenvPython
    if (Test-Path -LiteralPath $VenvPythonw) {
        $launchPython = $VenvPythonw
    }

    Set-Content -LiteralPath $LaunchLogFile -Value "" -Encoding UTF8
    Write-Log "Starting application..."

    $stderrHandle = [System.IO.File]::Open($LaunchLogFile, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        $process = Start-Process -FilePath $launchPython -ArgumentList @((Join-Path $ProjectRoot "run_gui.py")) -WorkingDirectory $ProjectRoot -RedirectStandardError $LaunchLogFile -PassThru
    } finally {
        $stderrHandle.Close()
    }

    Start-Sleep -Seconds 2
    if ($null -ne $process -and $null -ne $process.ExitCode -and $process.HasExited) {
        $details = ""
        if (Test-Path -LiteralPath $LaunchLogFile) {
            $details = (Get-Content -LiteralPath $LaunchLogFile -Raw -ErrorAction SilentlyContinue).Trim()
        }
        if (-not $details) {
            $details = "Application closed immediately with code $($process.ExitCode)."
        }
        throw "Application launch failed. Details: $details"
    }

    Write-Log "Application started."
}

Write-Log "=== Bootstrap Windows prerequisites + setup ==="

$pythonInfo = Ensure-Python
$rscriptPath = Ensure-Dependency `
    -Name "R" `
    -Finder ${function:Find-Rscript} `
    -WingetId "RProject.R" `
    -ManualHint "Install R with standard options, then run this script again."

$perlPath = Ensure-Dependency `
    -Name "Perl" `
    -Finder ${function:Find-Perl} `
    -WingetId "StrawberryPerl.StrawberryPerl" `
    -ManualHint "Install Strawberry Perl with standard options, then run this script again."

Write-Log "Detected prerequisites:"
Write-Log "  Python: $($pythonInfo.Display)"
Write-Log "  R: ${rscriptPath}"
Write-Log "  Perl: ${perlPath}"

Ensure-Venv -PythonInfo $pythonInfo
$torchMode = Ask-TorchMode
Write-Log "Selected Torch mode: $($torchMode.Label)"
Install-PythonDependencies -TorchMode $torchMode

if ($SkipRun) {
    Write-Log "Option -SkipRun active: application not started."
    exit 0
}

Launch-Application
Write-Log "Bootstrap finished successfully."
exit 0
