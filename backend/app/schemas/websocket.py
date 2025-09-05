"""
WebSocket相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Any, Dict, Optional
from enum import Enum


class CommandType(str, Enum):
    """命令类型枚举"""
    SYSTEM = "system"
    DEVICE = "device"
    HELP = "help"
    CLEAR = "clear"
    EXIT = "exit"


class WSMessageType(str, Enum):
    """WebSocket消息类型"""
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    INFO = "info"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    AUTO_AT = "auto_at"


class WSCommandMessage(BaseModel):
    """WebSocket命令消息"""
    type: WSMessageType = WSMessageType.COMMAND
    command: str
    args: Optional[list] = []
    timestamp: Optional[str] = None


class WSResponseMessage(BaseModel):
    """WebSocket响应消息"""
    type: WSMessageType
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str
    success: bool = True


class WSErrorMessage(BaseModel):
    """WebSocket错误消息"""
    type: WSMessageType = WSMessageType.ERROR
    error: str
    code: int = 500
    timestamp: str


class SendMessageRequest(BaseModel):
    """发送WebSocket消息请求"""
    message: str
    message_type: WSMessageType = WSMessageType.INFO
    data: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseModel):
    """发送WebSocket消息响应"""
    success: bool
    message: str
    sent_to_session: Optional[str] = None