"""
Session Management API Endpoints
会话管理API端点
"""

import logging
from fastapi import APIRouter, Request, Header, Depends
from typing import Optional

from app.core.response import APIResponse
from app.core.exceptions import SessionException
from app.services.session_service import session_service
from app.schemas.session_schemas import CreateSessionRequest

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_session_id_from_header(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
    """从请求头获取会话ID"""
    return x_session_id


@router.post("/create", response_model=APIResponse)
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


@router.post("/cleanup", response_model=APIResponse)
async def force_cleanup_sessions():
    """强制清理所有会话（管理员功能）"""
    success = await session_service.force_cleanup_session()
    return APIResponse.success(
        data={"cleaned": success},
        msg="会话清理成功" if success else "会话清理失败"
    )