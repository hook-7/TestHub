"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1.endpoints import serial, session, commands, health, workflow
from app.api.v1 import websocket

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, tags=["系统"])
api_router.include_router(session.router, prefix="/session", tags=["会话管理"])
api_router.include_router(serial.router, prefix="/serial", tags=["串口通信"])
api_router.include_router(commands.router, prefix="/commands", tags=["指令管理"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["工作流自动化"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket", "实时通信"])