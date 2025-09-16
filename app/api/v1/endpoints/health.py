"""
Health Check API Endpoints
健康检查API端点
"""

import logging
from fastapi import APIRouter, status
from app.core.response import APIResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="健康检查",
    description="检查应用程序的健康状态",
    tags=["系统"]
)
async def health_check():
    """健康检查端点"""
    return APIResponse.success(
        data={
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        },
        msg="系统运行正常"
    )


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="简单ping检查",
    description="简单的连通性检查",
    tags=["系统"]
)
async def ping():
    """简单的ping端点"""
    return {"ping": "pong"}