@echo off
REM TechnologySuccession ローカル起動（Windows）
REM docker compose build が失敗する環境向け: 先に docker build してから compose up

cd /d "%~dp0.."

echo === Building backend ===
docker build -t tech-succession-backend:latest ./backend
if errorlevel 1 exit /b 1

echo === Building frontend ===
docker build -t tech-succession-frontend:latest ./frontend
if errorlevel 1 (
  echo Frontend build failed. Starting postgres + backend only...
  docker compose up -d postgres backend --no-build
  exit /b 0
)

echo === Starting all services ===
docker compose up -d --no-build
if errorlevel 1 (
  echo.
  echo Port 8000 may be in use. Try:
  echo   docker ps
  echo   docker stop ^<container_name^>
  echo   set BACKEND_PORT=8001 ^&^& docker compose up -d postgres backend --no-build
  exit /b 1
)

echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
