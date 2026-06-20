#!/bin/bash
set -euo pipefail

# Start backend in the background
echo "Starting backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 5

# Start frontend development server
echo "Starting frontend..."
npm run dev --prefix frontend

# Wait for both processes to complete
wait