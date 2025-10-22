#!/bin/bash

# Build script for DTN project
# Creates production builds of both frontend and backend

set -e

echo "🏗️  Building DTN Project"
echo "======================="

# Check if we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
mkdir -p dist/

# Build backend
echo "🛰  Building backend..."
cd backend
python -m pip install -e .
python -m build --wheel --outdir ../dist/
cd ..

# Build frontend
echo "🌐 Building frontend..."
cd frontend
npm run build
cp -r dist/* ../dist/
cd ..

echo ""
echo "✅ Build complete!"
echo "   Output directory: dist/"
echo "   Backend wheel: dist/*.whl"
echo "   Frontend: dist/index.html"