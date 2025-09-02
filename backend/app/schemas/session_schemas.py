"""
Session Management Schemas
会话管理相关的数据模型
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str = Field(..., description="会话ID")
    client_ip: str = Field(..., description="客户端IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    is_active: bool = Field(True, description="是否活跃")


class SessionStatus(BaseModel):
    """会话状态"""
    has_active_session: bool = Field(..., description="是否有活跃会话")
    current_session: Optional[SessionInfo] = Field(None, description="当前会话信息")
    total_sessions: int = Field(0, description="总会话数")


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    client_info: Optional[str] = Field(None, description="客户端信息")


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str = Field(..., description="会话ID")
    token: str = Field(..., description="会话令牌")
    expires_in: int = Field(..., description="过期时间(秒)")