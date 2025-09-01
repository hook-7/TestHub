"""
Application Configuration
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Industrial HMI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Serial communication settings
    SERIAL_TIMEOUT: float = 1.0
    SERIAL_BAUDRATE: int = 9600
    SERIAL_BYTESIZE: int = 8
    SERIAL_PARITY: str = "N"  # None
    SERIAL_STOPBITS: int = 1
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()