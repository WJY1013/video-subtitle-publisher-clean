@echo off
REM GULF Video Subtitle Publisher - Windows Lightweight Startup (No Docker)
REM This script starts backend and frontend directly on Windows

echo.
echo ========================================
echo GULF Video Subtitle Publisher
echo Lightweight Version (No Docker Required)
echo ========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo Python is installed.

REM Check Node.js installation
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js is installed.

echo.
echo Setting up backend...
cd /d "%~dp0backend"

echo Installing Python dependencies...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies!
    pause
    exit /b 1
)

echo.
echo Starting Backend (FastAPI on port 8000)...
start cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd /d "%~dp0frontend"

echo.
echo Installing Node.js dependencies...
call npm install --quiet

if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies!
    pause
    exit /b 1
)

echo.
echo Starting Frontend (Next.js on port 3000)...
start cmd /k "npm run dev"

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

timeout /t 10 /nobreak

echo Opening browser...
start http://localhost:3000

echo.
echo All services started!
echo Close any terminal window to stop services.
pause
