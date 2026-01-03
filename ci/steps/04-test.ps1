# CI Step 4: Run Tests
# Executes unit and integration tests

param(
    [switch]$Coverage,
    [string]$TestPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 4: Run Tests ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment if exists
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Build pytest arguments
$pytestArgs = @("-v", "--tb=short")

if ($Coverage) {
    $pytestArgs += "--cov=src/ai_dev_orchestrator"
    $pytestArgs += "--cov=contracts"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=html:coverage_report"
}

# Determine test path
if ($TestPath) {
    $testDir = $TestPath
} else {
    $testDir = Join-Path $rootDir "tests"
}

# Run all tests
Write-Host "Running tests..." -ForegroundColor Yellow
pytest $testDir @pytestArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed"
    exit 1
}

Write-Host "=== Tests Complete ===" -ForegroundColor Cyan
