"""
Logging Configuration
"""

import logging
import sys
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")