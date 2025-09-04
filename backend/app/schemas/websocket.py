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
    # 工作流相关消息类型
    WORKFLOW_LOG = "workflow_log"
    WORKFLOW_CONFIRM = "workflow_confirm"
    WORKFLOW_STATUS = "workflow_status"


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


class WSWorkflowLogMessage(BaseModel):
    """工作流日志消息"""
    type: WSMessageType = WSMessageType.WORKFLOW_LOG
    execution_id: str
    step_id: str
    level: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class WSWorkflowConfirmMessage(BaseModel):
    """工作流确认消息"""
    type: WSMessageType = WSMessageType.WORKFLOW_CONFIRM
    execution_id: str
    step_id: str
    message: str
    options: list[str]
    timeout: Optional[float] = None
    timestamp: str


class WSWorkflowStatusMessage(BaseModel):
    """工作流状态消息"""
    type: WSMessageType = WSMessageType.WORKFLOW_STATUS
    execution_id: str
    status: str
    current_step: Optional[str] = None
    message: str
    timestamp: str