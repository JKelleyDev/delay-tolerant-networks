#!/bin/bash

# Start DTN Simulator Backend Server
echo "Starting DTN Simulator Backend..."

cd "$(dirname "$0")/../backend" || exit 1

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.8 or later."
    exit 1
fi

# Install dependencies if needed
if [ ! -f ".dependencies_installed" ]; then
    echo "Installing dependencies..."
    python -m pip install fastapi uvicorn pydantic
    if [ $? -eq 0 ]; then
        touch .dependencies_installed
        echo "Dependencies installed successfully."
    else
        echo "Failed to install dependencies."
        exit 1
    fi
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"

python -m src.main

echo "Backend server stopped."