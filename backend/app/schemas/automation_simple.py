"""
自动化命令相关的简化数据模型 (无外部依赖)
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import json


class CommandType(str, Enum):
    """命令类型枚举"""
    SYSTEM = "system"
    DEVICE = "device"
    TEST = "test"
    MAINTENANCE = "maintenance"


class CommandPriority(str, Enum):
    """命令优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CommandStatus(str, Enum):
    """命令执行状态"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseModel:
    """简化的BaseModel"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.model_dump(), ensure_ascii=False, indent=2)


class AutomationCommandRequest(BaseModel):
    """自动化命令请求"""
    def __init__(self, 
                 command_name: str,
                 command_type: CommandType,
                 priority: CommandPriority = CommandPriority.NORMAL,
                 parameters: Dict[str, Any] = None,
                 requires_confirmation: bool = True,
                 timeout_seconds: Optional[int] = 30,
                 description: Optional[str] = None,
                 operator_id: Optional[str] = None,
                 workstation_id: Optional[str] = None):
        super().__init__(
            command_name=command_name,
            command_type=command_type,
            priority=priority,
            parameters=parameters or {},
            requires_confirmation=requires_confirmation,
            timeout_seconds=timeout_seconds,
            description=description,
            operator_id=operator_id,
            workstation_id=workstation_id
        )


class AutomationCommandResponse(BaseModel):
    """自动化命令响应"""
    def __init__(self,
                 command_id: str,
                 status: CommandStatus,
                 result: Optional[Dict[str, Any]] = None,
                 error_message: Optional[str] = None,
                 execution_time: Optional[float] = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        super().__init__(
            command_id=command_id,
            status=status,
            result=result,
            error_message=error_message,
            execution_time=execution_time,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now()
        )


class CommandConfirmationRequest(BaseModel):
    """命令确认请求"""
    def __init__(self,
                 command_id: str,
                 confirmed: bool,
                 operator_notes: Optional[str] = None):
        super().__init__(
            command_id=command_id,
            confirmed=confirmed,
            operator_notes=operator_notes
        )


class CommandTemplate(BaseModel):
    """命令模板"""
    def __init__(self,
                 template_id: str,
                 name: str,
                 command_type: CommandType,
                 description: str,
                 parameters_schema: Dict[str, Any],
                 requires_confirmation: bool = True,
                 is_active: bool = True):
        super().__init__(
            template_id=template_id,
            name=name,
            command_type=command_type,
            description=description,
            parameters_schema=parameters_schema,
            requires_confirmation=requires_confirmation,
            is_active=is_active
        )