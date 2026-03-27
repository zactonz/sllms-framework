param(
    [string]$PythonExe = "python",
    [switch]$BootstrapAll
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"

if (!(Test-Path $Venv)) {
    & $PythonExe -m venv $Venv
}

$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")

if ($BootstrapAll) {
    & $VenvPython (Join-Path $Root "scripts\bootstrap.py") --all
}

Write-Host ""
Write-Host "Environment ready."
Write-Host "Next steps:"
if ($BootstrapAll) {
    Write-Host "1. Run: $VenvPython main.py --doctor"
    Write-Host "2. Run: $VenvPython main.py --once"
    Write-Host "3. Run: $VenvPython main.py --text `"open notepad`""
} else {
    Write-Host "1. Run: $VenvPython scripts\bootstrap.py --all"
    Write-Host "2. Run: $VenvPython main.py --doctor"
    Write-Host "3. Run: $VenvPython main.py --once"
}
