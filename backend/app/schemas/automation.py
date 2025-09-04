"""
自动化命令相关的数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class CommandType(str, Enum):
    """命令类型枚举"""
    SYSTEM = "system"  # 系统命令
    DEVICE = "device"  # 设备命令
    TEST = "test"      # 测试命令
    MAINTENANCE = "maintenance"  # 维护命令


class CommandPriority(str, Enum):
    """命令优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CommandStatus(str, Enum):
    """命令执行状态"""
    PENDING = "pending"      # 等待执行
    CONFIRMED = "confirmed"  # 用户已确认
    EXECUTING = "executing"  # 执行中
    SUCCESS = "success"      # 执行成功
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class AutomationCommandRequest(BaseModel):
    """自动化命令请求"""
    command_name: str = Field(..., description="命令名称")
    command_type: CommandType = Field(..., description="命令类型")
    priority: CommandPriority = Field(default=CommandPriority.NORMAL, description="优先级")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="命令参数")
    requires_confirmation: bool = Field(default=True, description="是否需要用户确认")
    timeout_seconds: Optional[int] = Field(default=30, description="超时时间(秒)")
    description: Optional[str] = Field(None, description="命令描述")
    operator_id: Optional[str] = Field(None, description="操作员ID")
    workstation_id: Optional[str] = Field(None, description="工位ID")


class AutomationCommandResponse(BaseModel):
    """自动化命令响应"""
    command_id: str = Field(..., description="命令ID")
    status: CommandStatus = Field(..., description="执行状态")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行耗时(秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CommandConfirmationRequest(BaseModel):
    """命令确认请求"""
    command_id: str = Field(..., description="命令ID")
    confirmed: bool = Field(..., description="是否确认执行")
    operator_notes: Optional[str] = Field(None, description="操作员备注")


class CommandListResponse(BaseModel):
    """命令列表响应"""
    commands: List[AutomationCommandResponse] = Field(..., description="命令列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


class CommandTemplate(BaseModel):
    """命令模板"""
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    command_type: CommandType = Field(..., description="命令类型")
    description: str = Field(..., description="模板描述")
    parameters_schema: Dict[str, Any] = Field(..., description="参数模式")
    requires_confirmation: bool = Field(default=True, description="是否需要确认")
    is_active: bool = Field(default=True, description="是否启用")