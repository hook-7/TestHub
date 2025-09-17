"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1.endpoints import commands, health, test_results, workflows, workflow_templates
from app.api.v1 import websocket

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, tags=["系统"])
api_router.include_router(commands.router, prefix="/commands", tags=["指令管理"])
api_router.include_router(test_results.router, prefix="/test-results", tags=["测试结果"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["工作流编排"])
api_router.include_router(workflow_templates.router, prefix="/workflow-templates", tags=["工作流模板"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket", "实时通信"])