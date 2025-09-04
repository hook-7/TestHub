"""
Session Management API Endpoints
会话管理API端点
"""

import logging
from fastapi import APIRouter, Request, Depends, status
from typing import Optional

from app.core.response import APIResponse
from app.core.dependencies import get_session_id_from_header
from app.services.session_service import session_service
from app.schemas.session_schemas import CreateSessionRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/create", 
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建会话",
    description="创建新的用户会话，用于后续的API认证",
    responses={
        201: {"description": "会话创建成功"},
        400: {"description": "参数错误"},
        500: {"description": "系统错误"}
    }
)
async def create_session(request: Request, session_request: CreateSessionRequest):
    """创建新会话（登录）"""
    session_response = await session_service.create_session(
        request=request,
        client_info=session_request.client_info
    )
    return APIResponse.success(data=session_response, msg="会话创建成功")


@router.delete("/destroy", response_model=APIResponse)
async def destroy_session(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """销毁会话（登出）"""
    if not session_id:
        return APIResponse.error(code=400, msg="缺少会话ID")
    
    await session_service.destroy_session(session_id, request)
    return APIResponse.success(msg="会话销毁成功")


@router.get("/status", response_model=APIResponse)
async def get_session_status():
    """获取会话状态"""
    status = await session_service.get_session_status()
    return APIResponse.success(data=status, msg="获取会话状态成功")


@router.post("/validate", response_model=APIResponse)
async def validate_session(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """验证会话有效性"""
    if not session_id:
        return APIResponse.error(code=400, msg="缺少会话ID")
    
    is_valid = await session_service.validate_session(session_id, request)
    return APIResponse.success(
        data={"valid": is_valid},
        msg="会话验证成功" if is_valid else "会话无效"
    )


@router.post("/heartbeat", response_model=APIResponse)
async def session_heartbeat(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """会话心跳 - 保持会话活跃"""
    if not session_id:
        return APIResponse.error(code=400, msg="缺少会话ID")
    
    try:
        is_valid = await session_service.update_session_activity(session_id, request)
        if is_valid:
            return APIResponse.success(
                data={"active": True, "last_activity": session_service.get_session_last_activity(session_id)},
                msg="心跳更新成功"
            )
        else:
            return APIResponse.error(code=401, msg="会话无效或已过期")
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return APIResponse.error(code=500, msg="心跳更新失败")


@router.post("/cleanup", response_model=APIResponse)
async def force_cleanup_sessions():
    """强制清理所有会话（已禁用 - 为保证系统安全）"""
    return APIResponse.error(
        code=403,
        msg="为保证系统安全，强制清理会话功能已被禁用。请等待会话自然超时或用户主动退出。"
    )