#!/bin/bash

# Development startup script for DTN project
# Starts both backend API server and frontend dev server

set -e

echo "🚀 Starting DTN Development Environment"
echo "======================================="

# Check if we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "🧹 Cleaning up..."
    jobs -p | xargs -r kill
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend API server
echo "🛰  Starting backend API server..."
cd backend/src
python -m dtn.api.server &
BACKEND_PID=$!
cd ../..

# Wait a moment for backend to start
sleep 3

# Start frontend dev server  
echo "🌐 Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Development servers started!"
echo "   Backend API: http://localhost:5001"
echo "   Frontend:    http://localhost:5173"
echo "   Health Check: curl http://localhost:5001/api/health"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait