$ErrorActionPreference = "Stop"
$DashboardRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = "$DashboardRoot\backend"
$Frontend = "$DashboardRoot\frontend"

if (-not (Test-Path "$Backend\.venv\Scripts\python.exe")) {
    throw "Backend environment not found. Run .\setup-dashboard.ps1 first."
}

if (-not (Test-Path "$Backend\.env")) {
    throw "Backend .env not found. Run setup-dashboard.ps1 and configure WASTENET_MODEL_PATH."
}

if (-not (Test-Path "$Frontend\node_modules")) {
    throw "Frontend node_modules not found. Run .\setup-dashboard.ps1 first."
}

Write-Host "Starting WasteNet backend and frontend..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Backend'; .\.venv\Scripts\python.exe run.py"
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Frontend'; npm run dev"
)

Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "Open the frontend URL after both terminals report that they are ready." -ForegroundColor Yellow
