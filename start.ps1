# Start AI Dev Orchestrator
# Runs both backend and frontend

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Dev Orchestrator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot

# Check if frontend dependencies are installed
$frontendDir = Join-Path $rootDir "frontend"
$nodeModules = Join-Path $frontendDir "node_modules"

if (-not (Test-Path $nodeModules) -and -not $BackendOnly) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

# Start Backend
if (-not $FrontendOnly) {
    Write-Host "Starting Backend on http://localhost:8100..." -ForegroundColor Green
    $backendDir = Join-Path $rootDir "backend"
    
    # Set workspace root to current directory (for artifact scanning)
    $env:WORKSPACE_ROOT = $rootDir
    
    # Use port 8100 to avoid conflict with engineering-tools (8000)
    Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$backendDir'; uvicorn main:app --reload --host 0.0.0.0 --port 8100"
}

# Start Frontend
if (-not $BackendOnly) {
    Write-Host "Starting Frontend on http://localhost:5173..." -ForegroundColor Green
    
    Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$frontendDir'; npm run dev"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  AI Dev Orchestrator Starting..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:8100" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8100/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  (Using ports 8100/5173 to avoid conflicts" -ForegroundColor DarkGray
Write-Host "   with engineering-tools on 8000/3000)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Keep script running
while ($true) {
    Start-Sleep -Seconds 10
}
