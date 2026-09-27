@echo off
REM GULF Video Subtitle Publisher - Windows Startup Script
REM This script starts all required services

echo.
echo ========================================
echo GULF Video Subtitle Publisher
echo Starting all services...
echo ========================================
echo.

REM Check if Docker is running
echo Checking Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running.
echo.

REM Start Docker Compose services
echo Starting Docker containers (PostgreSQL, Redis, MinIO)...
docker-compose up -d

if errorlevel 1 (
    echo ERROR: Failed to start Docker containers!
    pause
    exit /b 1
)

echo Waiting for services to be ready...
timeout /t 10 /nobreak

REM Start backend in a new terminal window
echo.
echo Starting Backend (FastAPI on port 8000)...
start cmd /k "cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Start frontend in a new terminal window
echo Starting Frontend (Next.js on port 3000)...
start cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ========================================
echo Services starting...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Please wait 30 seconds for services to fully start.
echo ========================================
echo.

timeout /t 5 /nobreak

echo Opening browser...
start http://localhost:3000

echo.
echo All services started!
echo Close any terminal window to stop services.
pause
