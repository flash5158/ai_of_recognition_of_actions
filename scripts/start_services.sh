#!/bin/bash
set -e
cd "$(dirname "$0")/.."
# Kill old processes
pkill -f uvicorn || true
pkill -f "next dev" || true
# Start backend
export OPENCV_AVFOUNDATION_SKIP_AUTH=1
nohup python -m uvicorn server:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
echo "BACKEND_STARTED:$!"
# Start frontend
cd dashboard
nohup npm run dev > ../frontend.log 2>&1 &
echo "FRONTEND_STARTED"
