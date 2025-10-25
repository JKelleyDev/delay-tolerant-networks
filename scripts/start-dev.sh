#!/bin/bash

# Start both backend and frontend servers for development
echo "Starting DTN Simulator Development Environment..."

# Check if required commands are available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.8 or later."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found. Please install Node.js 18 or later."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down development servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Trap cleanup on script exit
trap cleanup SIGINT SIGTERM

# Get the script directory
SCRIPT_DIR="$(dirname "$0")"

# Start backend server in background
echo "Starting backend server..."
"$SCRIPT_DIR/start-backend.sh" &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server in background
echo "Starting frontend server..."
"$SCRIPT_DIR/start-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "🚀 DTN Simulator Development Environment Started!"
echo "📖 Backend API: http://localhost:8000/docs"
echo "🌐 Frontend App: http://localhost:3000"
echo "📊 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID