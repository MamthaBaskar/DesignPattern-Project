#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python backend dependencies
pip install -r requirements.txt

# Build frontend with npm if available
if command -v npm &> /dev/null; then
    echo "Building frontend with npm..."
    npm --prefix frontend install
    npm --prefix frontend run build
elif [ -d "frontend/dist" ]; then
    echo "Using existing pre-built frontend assets in frontend/dist"
else
    echo "Error: npm is not available and frontend/dist was not found"
    exit 1
fi

echo "Build completed successfully!"

