#!/bin/bash
# GULF Video Subtitle Publisher - macOS/Linux Startup Script

echo ""
echo "========================================"
echo "GULF Video Subtitle Publisher"
echo "Starting all services..."
echo "========================================"
echo ""

# Check if Docker is running
echo "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker Desktop first."
    exit 1
fi

echo "Docker is running."
echo ""

# Start Docker Compose services
echo "Starting Docker containers (PostgreSQL, Redis, MinIO)..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start Docker containers!"
    exit 1
fi

echo "Waiting for services to be ready..."
sleep 10

# Start backend
echo ""
echo "Starting Backend (FastAPI on port 8000)..."
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting Frontend (Next.js on port 3000)..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

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
