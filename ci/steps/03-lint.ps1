# CI Step 3: Linting
# Runs code quality checks

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 3: Linting ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment if exists
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Run Ruff (fast Python linter)
Write-Host "Running Ruff linter..." -ForegroundColor Yellow
$srcDir = Join-Path $rootDir "src"
$testsDir = Join-Path $rootDir "tests"
$contractsDir = Join-Path $rootDir "contracts"

ruff check $srcDir $testsDir $contractsDir --ignore E501
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Ruff found issues (non-blocking)"
}

# Run Ruff format check
Write-Host "Checking code formatting..." -ForegroundColor Yellow
ruff format --check $srcDir $testsDir $contractsDir
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Code formatting issues found. Run 'ruff format .' to fix."
}

Write-Host "=== Linting Complete ===" -ForegroundColor Cyan
