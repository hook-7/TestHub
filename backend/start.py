#!/usr/bin/env python3
"""
Industrial HMI Application Launcher
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add backend app to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.main import app

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Server: http://{settings.HOST}:{settings.PORT}")
    print(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    # Detect if running as PyInstaller executable
    is_packaged = getattr(sys, 'frozen', False)
    if is_packaged:
        uvicorn.run(
        app,  
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True,
    )
    else:
        uvicorn.run(
            "app.main:app",  
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,  
            log_level="info" if not settings.DEBUG else "debug",
            access_log=True,
        )