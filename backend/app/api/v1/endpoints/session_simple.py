"""
简化的会话管理API端点
避免登录阻塞问题
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Request
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

# 简化的会话存储
simple_sessions = {}

@router.get("/status")
async def get_session_status_simple():
    """
    简化的会话状态检查
    """
    try:
        return {
            "code": 0,
            "msg": "获取会话状态成功",
            "data": {
                "has_active_session": len(simple_sessions) > 0,
                "current_session": None,
                "session_count": len(simple_sessions)
            }
        }
    except Exception as e:
        logger.error(f"获取会话状态失败: {e}")
        return {
            "code": 500,
            "msg": f"获取会话状态失败: {str(e)}",
            "data": None
        }


@router.post("/create")
async def create_session_simple(request: Request, session_data: dict):
    """
    简化的创建会话
    """
    try:
        # 生成会话信息
        session_id = str(uuid.uuid4())
        token = f"token_{session_id[:8]}"
        
        # 存储会话
        session_info = {
            "session_id": session_id,
            "token": token,
            "client_info": session_data.get("client_info", "Unknown"),
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        simple_sessions[session_id] = session_info
        
        return {
            "code": 0,
            "msg": "会话创建成功",
            "data": {
                "session_id": session_id,
                "token": token,
                "expires_in": 3600
            }
        }
        
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return {
            "code": 500,
            "msg": f"创建会话失败: {str(e)}",
            "data": None
        }


@router.post("/validate")
async def validate_session_simple(session_data: dict):
    """
    简化的会话验证
    """
    try:
        session_id = session_data.get("session_id")
        
        if not session_id:
            return {
                "code": 400,
                "msg": "缺少会话ID",
                "data": None
            }
        
        if session_id in simple_sessions:
            # 更新最后活动时间
            simple_sessions[session_id]["last_activity"] = datetime.now().isoformat()
            
            return {
                "code": 0,
                "msg": "会话验证成功",
                "data": {
                    "valid": True,
                    "session_id": session_id
                }
            }
        else:
            return {
                "code": 404,
                "msg": "会话不存在",
                "data": {
                    "valid": False
                }
            }
            
    except Exception as e:
        logger.error(f"会话验证失败: {e}")
        return {
            "code": 500,
            "msg": f"会话验证失败: {str(e)}",
            "data": None
        }


@router.delete("/destroy")
async def destroy_session_simple(session_data: dict):
    """
    简化的销毁会话
    """
    try:
        session_id = session_data.get("session_id")
        
        if session_id and session_id in simple_sessions:
            del simple_sessions[session_id]
            return {
                "code": 0,
                "msg": "会话销毁成功",
                "data": None
            }
        else:
            return {
                "code": 404,
                "msg": "会话不存在",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"销毁会话失败: {e}")
        return {
            "code": 500,
            "msg": f"销毁会话失败: {str(e)}",
            "data": None
        }


@router.post("/heartbeat")
async def session_heartbeat_simple(session_data: dict):
    """
    简化的会话心跳
    """
    try:
        session_id = session_data.get("session_id")
        
        if session_id and session_id in simple_sessions:
            # 更新最后活动时间
            simple_sessions[session_id]["last_activity"] = datetime.now().isoformat()
            
            return {
                "code": 0,
                "msg": "心跳成功",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            return {
                "code": 404,
                "msg": "会话不存在",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"心跳失败: {e}")
        return {
            "code": 500,
            "msg": f"心跳失败: {str(e)}",
            "data": None
        }


@router.post("/force-cleanup")
async def force_cleanup_simple():
    """
    强制清理所有会话
    """
    try:
        session_count = len(simple_sessions)
        simple_sessions.clear()
        
        return {
            "code": 0,
            "msg": "强制清理完成",
            "data": {
                "cleaned": True,
                "cleaned_count": session_count
            }
        }
        
    except Exception as e:
        logger.error(f"强制清理失败: {e}")
        return {
            "code": 500,
            "msg": f"强制清理失败: {str(e)}",
            "data": None
        }