#!/bin/bash
# Industrial HMI Startup Script

set -e

echo "🏭 Industrial HMI - 工业上位机系统"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Set PATH for uv
export PATH="$HOME/.local/bin:$PATH"

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
uv sync

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    echo "🎨 Building frontend..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    npm run build
    cd "$SCRIPT_DIR"
fi

echo ""
echo "🚀 Starting Industrial HMI..."
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop..."

# Start the application
uv run python backend/start.py