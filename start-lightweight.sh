#!/bin/bash
# GULF Video Subtitle Publisher - macOS/Linux Lightweight Startup (No Docker)

echo ""
echo "========================================"
echo "GULF Video Subtitle Publisher"
echo "Lightweight Version (No Docker Required)"
echo "========================================"
echo ""

# Check Python installation
echo "Checking Python installation..."
if ! python3 --version > /dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi
echo "Python is installed: $(python3 --version)"

# Check Node.js installation
echo "Checking Node.js installation..."
if ! node --version > /dev/null 2>&1; then
    echo "ERROR: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo "Node.js is installed: $(node --version)"

echo ""
echo "Setting up backend..."
cd "$(dirname "$0")/backend"

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies!"
    exit 1
fi

echo ""
echo "Starting Backend (FastAPI on port 8000)..."
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$(dirname "$0")/frontend"

echo ""
echo "Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Node.js dependencies!"
    exit 1
fi

echo ""
echo "Starting Frontend (Next.js on port 3000)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Services starting..."
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Please wait 30 seconds for services to fully start."
echo "========================================"
echo ""

sleep 5

echo "Opening browser..."
open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000

echo ""
echo "All services started!"
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for signals
wait
