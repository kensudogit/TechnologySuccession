# TechnologySuccession ローカル起動（PowerShell）
# docker compose build が失敗する環境向け

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Building backend ===" -ForegroundColor Cyan
docker build -t tech-succession-backend:latest ./backend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Building frontend ===" -ForegroundColor Cyan
docker build -t tech-succession-frontend:latest ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed. Starting postgres + backend only..." -ForegroundColor Yellow
    docker compose up -d postgres backend --no-build
    exit 0
}

Write-Host "=== Starting all services ===" -ForegroundColor Cyan
docker compose up -d --no-build

Write-Host ""
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"
