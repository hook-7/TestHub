#!/bin/bash
# Development startup script

echo "🚀 Starting Industrial HMI in development mode..."

# Set PATH for uv
export PATH="$HOME/.local/bin:$PATH"

# Start backend
echo "📡 Starting FastAPI backend..."
cd /workspace
source .venv/bin/activate 2>/dev/null || echo "Virtual env not found, using uv run"
uv run python start.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting Vue3 frontend..."
cd /workspace/frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo "✅ Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Trap Ctrl+C to kill both processes
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for processes
wait