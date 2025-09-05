"""
Command Schemas
常用指令相关的数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class SavedCommand(BaseModel):
    """保存的指令模型"""
    id: str = Field(..., description="指令唯一标识")
    name: str = Field(..., description="指令显示名称")
    command: str = Field(..., description="实际指令内容")
    description: str = Field(default="", description="指令描述")
    expected_response: str = Field(default="", description="期望返回值")
    send_as_hex: bool = Field(default=False, description="是否以原始16进制发送")
    show_notification: bool = Field(default=False, description="是否弹出通知")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)
    
    model_config = {
        "from_attributes": True
    }


class CreateCommandRequest(BaseModel):
    """创建指令请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="指令显示名称")
    command: str = Field(..., min_length=1, max_length=200, description="实际指令内容")
    description: str = Field(default="", max_length=200, description="指令描述")
    expected_response: str = Field(default="", max_length=1000, description="期望返回值")
    send_as_hex: bool = Field(default=False, description="是否以原始16进制发送")
    show_notification: bool = Field(default=False, description="是否弹出通知")


class UpdateCommandRequest(BaseModel):
    """更新指令请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="指令显示名称")
    command: Optional[str] = Field(None, min_length=1, max_length=200, description="实际指令内容")
    description: Optional[str] = Field(None, max_length=200, description="指令描述")
    expected_response: Optional[str] = Field(None, max_length=1000, description="期望返回值")
    send_as_hex: Optional[bool] = Field(None, description="是否以原始16进制发送")
    show_notification: Optional[bool] = Field(None, description="是否弹出通知")


class CommandsListResponse(BaseModel):
    """指令列表响应模型"""
    commands: List[SavedCommand] = Field(default=[], description="指令列表")
    total: int = Field(default=0, description="指令总数")
