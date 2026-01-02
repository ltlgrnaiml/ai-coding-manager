# CI Step 2: Install Dependencies
# Installs project dependencies

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 2: Install Dependencies ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Check for uv
$hasUv = Get-Command uv -ErrorAction SilentlyContinue

if ($hasUv) {
    Write-Host "Installing dependencies with uv..." -ForegroundColor Yellow
    Push-Location $rootDir
    uv sync --all-extras
    Pop-Location
} else {
    Write-Host "Installing dependencies with pip..." -ForegroundColor Yellow
    
    # Create virtual environment if it doesn't exist
    $venvPath = Join-Path $rootDir ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv $venvPath
    }
    
    # Activate and install
    $activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
    . $activateScript
    
    pip install -e ".[all]" --quiet
}

Write-Host "=== Dependencies Installed ===" -ForegroundColor Cyan
