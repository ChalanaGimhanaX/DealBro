#!/bin/bash

# Start script for DealBro backend services

set -e

echo "================================"
echo "Starting DealBro Backend"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run setup.py first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

echo ""
echo "Starting API server on port 8000..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "API server started (PID: $API_PID)"
echo ""
echo "To start the ingestion scheduler, run:"
echo "  python -m app.ingestion.scheduler"
echo ""
echo "Press Ctrl+C to stop the API server"

# Wait for API server
wait $API_PID
