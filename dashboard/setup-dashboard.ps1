$ErrorActionPreference = "Stop"
$DashboardRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== WasteNet Dashboard Setup ===" -ForegroundColor Cyan

Push-Location "$DashboardRoot\backend"
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        py -m venv .venv
    }

    Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt

    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created backend .env from example." -ForegroundColor Green
    }
}
finally {
    Pop-Location
}

Push-Location "$DashboardRoot\frontend"
try {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install

    if (-not (Test-Path ".env.local")) {
        Copy-Item ".env.local.example" ".env.local"
        Write-Host "Created frontend .env.local from example." -ForegroundColor Green
    }
}
finally {
    Pop-Location
}

Write-Host "" 
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "IMPORTANT: Open dashboard\backend\.env and verify WASTENET_MODEL_PATH before running." -ForegroundColor Yellow
