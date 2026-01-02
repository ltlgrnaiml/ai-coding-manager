# CI Step 1: Setup
# Validates the environment

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 1: Setup ===" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion"

# Ensure Python 3.11+
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Error "Python 3.11+ required. Found: $pythonVersion"
        exit 1
    }
}

# Check for uv (preferred) or pip
Write-Host "Checking package manager..." -ForegroundColor Yellow
$hasUv = Get-Command uv -ErrorAction SilentlyContinue
if ($hasUv) {
    Write-Host "  Using uv package manager" -ForegroundColor Green
} else {
    Write-Host "  Using pip (uv recommended for faster installs)" -ForegroundColor Yellow
}

Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
