"""
Session Management Service
会话管理服务 - 实现单用户串口连接限制
"""

import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request

from app.core.exceptions import SessionException, ErrorCode
from app.core.config import settings
from app.schemas.session_schemas import (
    SessionInfo, SessionStatus, SessionResponse
)

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务 - 确保同时只有一个客户端可以连接串口"""
    
    def __init__(self):
        # 内存存储活跃会话（生产环境建议使用Redis）
        self._active_session: Optional[SessionInfo] = None
        self._heartbeat_timeout_seconds = settings.HEARTBEAT_TIMEOUT_SECONDS  # 心跳超时时间（秒）
    
    def _generate_session_id(self) -> str:
        """生成唯一会话ID"""
        return str(uuid.uuid4())
    
    def _generate_token(self, session_id: str, client_ip: str) -> str:
        """生成会话令牌"""
        data = f"{session_id}:{client_ip}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _is_session_expired(self, session: SessionInfo) -> bool:
        """检查会话是否过期（基于心跳超时）"""
        timeout_delta = timedelta(seconds=self._heartbeat_timeout_seconds)
        return datetime.now() - session.last_activity > timeout_delta
    
    def _cleanup_expired_session(self) -> None:
        """清理过期会话（基于心跳超时）"""
        if self._active_session and self._is_session_expired(self._active_session):
            logger.info(f"Session {self._active_session.session_id} expired due to heartbeat timeout, cleaning up")
            self._active_session = None
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先获取真实IP（考虑代理情况）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 回退到直接连接IP
        return request.client.host if request.client else "unknown"
    
    async def create_session(self, request: Request, client_info: Optional[str] = None) -> SessionResponse:
        """创建新会话（如果没有活跃会话）"""
        try:
            # 清理过期会话
            self._cleanup_expired_session()
            
            # 检查是否已有活跃会话
            if self._active_session:
                logger.warning(f"Attempt to create session while active session exists: {self._active_session.session_id}")
                raise SessionException(
                    ErrorCode.SESSION_ALREADY_EXISTS,
                    f"已有客户端连接中（IP: {self._active_session.client_ip}），为保证系统安全，请等待其主动退出或会话超时后再试"
                )
            
            # 创建新会话
            session_id = self._generate_session_id()
            client_ip = self.get_client_ip(request)
            user_agent = request.headers.get("User-Agent")
            now = datetime.now()
            
            session_info = SessionInfo(
                session_id=session_id,
                client_ip=client_ip,
                user_agent=user_agent,
                created_at=now,
                last_activity=now,
                is_active=True
            )
            
            # 存储会话
            self._active_session = session_info
            
            # 生成令牌
            token = self._generate_token(session_id, client_ip)
            
            logger.info(f"Created new session: {session_id} for client: {client_ip}")
            
            return SessionResponse(
                session_id=session_id,
                token=token,
                expires_in=self._heartbeat_timeout_seconds
            )
            
        except SessionException:
            raise
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise SessionException(ErrorCode.SYSTEM_ERROR, f"创建会话失败: {str(e)}")
    
    async def validate_session(self, session_id: str, request: Request) -> bool:
        """验证会话有效性（不更新活动时间，只有心跳才更新）"""
        try:
            # 清理过期会话
            self._cleanup_expired_session()
            
            if not self._active_session:
                return False
            
            # 检查会话ID
            if self._active_session.session_id != session_id:
                return False
            
            # 检查客户端IP（可选，增强安全性）
            client_ip = self.get_client_ip(request)
            if self._active_session.client_ip != client_ip:
                logger.warning(f"IP mismatch for session {session_id}: expected {self._active_session.client_ip}, got {client_ip}")
                return False
            
            # 注意：这里不更新 last_activity 时间，只有心跳接口才能更新
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    async def destroy_session(self, session_id: str, request: Request) -> bool:
        """销毁会话"""
        try:
            if not self._active_session:
                return True
            
            if self._active_session.session_id != session_id:
                logger.warning(f"Attempt to destroy non-matching session: {session_id}")
                return False
            
            # 验证客户端IP
            client_ip = self.get_client_ip(request)
            if self._active_session.client_ip != client_ip:
                logger.warning(f"IP mismatch for session destruction: expected {self._active_session.client_ip}, got {client_ip}")
                raise SessionException(ErrorCode.SESSION_ACCESS_DENIED, "会话访问被拒绝")
            
            logger.info(f"Destroying session: {session_id}")
            self._active_session = None
            
            return True
            
        except SessionException:
            raise
        except Exception as e:
            logger.error(f"Error destroying session: {e}")
            raise SessionException(ErrorCode.SYSTEM_ERROR, f"销毁会话失败: {str(e)}")
    
    async def get_session_status(self) -> SessionStatus:
        """获取会话状态"""
        try:
            # 清理过期会话
            self._cleanup_expired_session()
            
            return SessionStatus(
                has_active_session=self._active_session is not None,
                current_session=self._active_session,
                total_sessions=1 if self._active_session else 0
            )
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            raise SessionException(ErrorCode.SYSTEM_ERROR, f"获取会话状态失败: {str(e)}")
    
    async def update_session_activity(self, session_id: str, request: Request) -> bool:
        """更新会话活动时间（心跳）"""
        try:
            # 清理过期会话
            self._cleanup_expired_session()
            
            if not self._active_session:
                return False
            
            # 检查会话ID
            if self._active_session.session_id != session_id:
                return False
            
            # 检查客户端IP（增强安全性）
            client_ip = self.get_client_ip(request)
            if self._active_session.client_ip != client_ip:
                logger.warning(f"IP mismatch for heartbeat {session_id}: expected {self._active_session.client_ip}, got {client_ip}")
                return False
            
            # 更新最后活动时间
            self._active_session.last_activity = datetime.now()
            logger.debug(f"Session heartbeat updated: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False
    
    def get_session_last_activity(self, session_id: str) -> Optional[str]:
        """获取会话最后活动时间"""
        if self._active_session and self._active_session.session_id == session_id:
            return self._active_session.last_activity.isoformat()
        return None
    
    def get_session_timeout_remaining(self, session_id: str) -> Optional[int]:
        """获取会话剩余心跳超时时间（秒）"""
        if self._active_session and self._active_session.session_id == session_id:
            timeout_delta = timedelta(seconds=self._heartbeat_timeout_seconds)
            remaining = timeout_delta - (datetime.now() - self._active_session.last_activity)
            return max(0, int(remaining.total_seconds()))
        return None

    async def force_cleanup_session(self) -> bool:
        """强制清理所有会话（已禁用功能）"""
        logger.warning("Force cleanup session attempted but is disabled for security reasons")
        return False


# Global service instance
session_service = SessionService()