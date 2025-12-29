#!/bin/bash

echo "========================================"
echo "  AI Copilot - PassAI"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python -m venv venv
    echo ""
fi

# Activate venv
echo "Activating virtual environment..."
source venv/Scripts/activate || source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt
echo ""

echo "Starting Backend and Frontend..."
echo ""

# Start backend in background
cd backend
python server.py &
BACKEND_PID=$!
cd ..

# Wait 3 seconds for backend to initialize
sleep 3

# Start frontend
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both services started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Backend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for processes
wait
