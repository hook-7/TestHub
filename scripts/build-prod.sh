#!/bin/bash
# Production build script

echo "🏗️ Building Industrial HMI for production..."

# Set PATH for uv
export PATH="$HOME/.local/bin:$PATH"

# Build frontend
echo "📦 Building frontend..."
cd /workspace/frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
    echo "📁 Built files are in: frontend/dist"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Test backend
echo "🧪 Testing backend..."
cd /workspace
uv run python -c "
import sys
sys.path.insert(0, 'backend')
from app.main import app
print('✅ Backend imports successful')
"

if [ $? -eq 0 ]; then
    echo "✅ Backend validation successful"
else
    echo "❌ Backend validation failed"
    exit 1
fi

echo "🎉 Production build completed!"
echo "To start production server:"
echo "  cd /workspace && uv run python start.py"