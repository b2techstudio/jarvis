$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Environnement virtuel absent. Crée-le avec : python -m venv .venv"
}

& $python (Join-Path $PSScriptRoot "generate_icon.py")
& $python -m PyInstaller --clean --noconfirm (Join-Path $projectRoot "jarvis-desktop.spec")

$releaseDir = Join-Path $projectRoot "dist\JARVIS-Desktop"
Copy-Item -LiteralPath (Join-Path $projectRoot ".env.example") -Destination (Join-Path $releaseDir ".env.example") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination (Join-Path $releaseDir "README.md") -Force

Write-Host "Build terminé : $releaseDir\JARVIS-Desktop.exe"
