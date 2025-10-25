#!/bin/bash

# Start DTN Simulator Frontend
echo "Starting DTN Simulator Frontend..."

cd "$(dirname "$0")/../frontend" || exit 1

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found. Please install Node.js 18 or later."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm not found. Please install npm."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        exit 1
    fi
fi

# Start the development server
echo "Starting frontend development server on http://localhost:3000"
echo "Make sure the backend server is running on http://localhost:8000"
echo "Press Ctrl+C to stop the server"

npm run dev

echo "Frontend server stopped."