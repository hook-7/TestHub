"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1.endpoints import serial, session, serial_login
from app.api.v1 import websocket

api_router = APIRouter()

# Include route modules
api_router.include_router(session.router, prefix="/session", tags=["session"])
api_router.include_router(serial.router, prefix="/serial", tags=["serial"])
api_router.include_router(serial_login.router, prefix="/serial-login", tags=["serial-login"])
api_router.include_router(websocket.router, prefix="/terminal", tags=["websocket", "terminal"])