"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1.endpoints import serial

api_router = APIRouter()

# Include route modules
api_router.include_router(serial.router, prefix="/serial", tags=["serial"])