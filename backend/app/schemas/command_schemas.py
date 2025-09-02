"""
Command Schemas
常用指令相关的数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SavedCommand(BaseModel):
    """保存的指令模型"""
    id: str = Field(..., description="指令唯一标识")
    name: str = Field(..., description="指令显示名称")
    command: str = Field(..., description="实际指令内容")
    description: str = Field(default="", description="指令描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: int(v.timestamp() * 1000)  # 转换为毫秒时间戳
        }


class CreateCommandRequest(BaseModel):
    """创建指令请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="指令显示名称")
    command: str = Field(..., min_length=1, max_length=200, description="实际指令内容")
    description: str = Field(default="", max_length=200, description="指令描述")


class UpdateCommandRequest(BaseModel):
    """更新指令请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="指令显示名称")
    command: Optional[str] = Field(None, min_length=1, max_length=200, description="实际指令内容")
    description: Optional[str] = Field(None, max_length=200, description="指令描述")


class CommandsListResponse(BaseModel):
    """指令列表响应模型"""
    commands: List[SavedCommand] = Field(default=[], description="指令列表")
    total: int = Field(default=0, description="指令总数")
