"""
Common Dependencies for FastAPI Endpoints
公共依赖项，避免代码重复
"""

from fastapi import Header, Depends, HTTPException, Request
from typing import Optional

from app.services.session_service import session_service


async def get_session_id_from_header(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
    """从请求头获取会话ID"""
    return x_session_id


async def validate_session_dependency(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
) -> str:
    """会话验证依赖 - 统一的会话验证逻辑"""
    if not session_id:
        raise HTTPException(status_code=401, detail="缺少会话ID，请先登录")
    
    is_valid = await session_service.validate_session(session_id, request)
    if not is_valid:
        raise HTTPException(status_code=401, detail="会话无效或已过期，请重新登录")
    
    return session_id


async def optional_session_dependency(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
) -> Optional[str]:
    """可选的会话验证依赖 - 用于不强制要求登录的端点"""
    if not session_id:
        return None
    
    is_valid = await session_service.validate_session(session_id, request)
    return session_id if is_valid else None