# Sync from Engineering-Tools
# Monitors upstream repo for changes and generates AI-readable TODO lists

param(
    [string]$Since,
    [switch]$UpdateState,
    [switch]$ShowState,
    [switch]$Quick  # Just last 10 commits
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Engineering-Tools Sync Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Join-Path $PSScriptRoot "scripts/sync_from_upstream.py"

$syncArgs = @()

if ($ShowState) {
    $syncArgs += "--show-state"
}
elseif ($Since) {
    $syncArgs += "--since", $Since
}
elseif ($Quick) {
    $syncArgs += "--since", "HEAD~10"
}

if ($UpdateState) {
    $syncArgs += "--update-state"
}

python $scriptPath @syncArgs

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Sync Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "TODO files saved to: .sync_todos/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Usage:" -ForegroundColor DarkGray
Write-Host "  .\sync.ps1              # Full sync since last checkpoint" -ForegroundColor DarkGray
Write-Host "  .\sync.ps1 -Quick       # Just last 10 commits" -ForegroundColor DarkGray
Write-Host "  .\sync.ps1 -UpdateState # Mark current HEAD as synced" -ForegroundColor DarkGray
Write-Host "  .\sync.ps1 -ShowState   # Show sync state" -ForegroundColor DarkGray
