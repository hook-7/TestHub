"""
TCP连接相关的数据模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class TcpConnectionConfig(BaseModel):
    """TCP连接配置模型"""
    host: str = Field(..., description="IP地址")
    port: int = Field(..., ge=1, le=65535, description="端口号")
    timeout: int = Field(default=5, ge=1, le=30, description="连接超时时间(秒)")
    auto_reconnect: bool = Field(default=True, description="是否自动重连")


class TcpConnection(BaseModel):
    """TCP连接模型"""
    id: str = Field(..., description="连接唯一标识")
    host: str = Field(..., description="IP地址")
    port: int = Field(..., description="端口号")
    timeout: int = Field(..., description="连接超时时间(秒)")
    auto_reconnect: bool = Field(..., description="是否自动重连")
    connected: bool = Field(default=False, description="连接状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")


class TcpCommandRequest(BaseModel):
    """TCP命令请求模型"""
    connection_id: str = Field(..., description="TCP连接ID")
    command: str = Field(..., description="要发送的命令")
    auto_add_crlf: bool = Field(default=True, description="是否自动添加\\r\\n")


class TcpCommandResponse(BaseModel):
    """TCP命令响应模型"""
    success: bool = Field(..., description="命令是否成功")
    response: str = Field(..., description="设备响应内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class TcpConnectionsListResponse(BaseModel):
    """TCP连接列表响应模型"""
    connections: List[TcpConnection] = Field(default=[], description="TCP连接列表")
    total: int = Field(default=0, description="连接总数")