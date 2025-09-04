"""
工作流相关的数据模型定义
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from enum import Enum


class StepType(str, Enum):
    """步骤类型枚举"""
    SEND = "send"
    EXPECT = "expect"
    ASSIGN = "assign"
    CONFIRM = "confirm"
    CONTROL = "control"


class ExpectType(str, Enum):
    """期望匹配类型"""
    STRING = "string"
    REGEX = "regex"
    TIMEOUT = "timeout"


class ControlType(str, Enum):
    """控制类型"""
    IF = "if"
    LOOP = "loop"
    BREAK = "break"
    CONTINUE = "continue"


class WorkflowStepBase(BaseModel):
    """工作流步骤基础模型"""
    id: str = Field(..., description="步骤唯一标识")
    name: str = Field(..., description="步骤名称")
    type: StepType = Field(..., description="步骤类型")
    description: Optional[str] = Field(None, description="步骤描述")


class SendStep(WorkflowStepBase):
    """发送指令步骤"""
    type: StepType = Field(StepType.SEND, description="步骤类型")
    command: str = Field(..., description="要发送的指令，支持变量占位符")
    port: Optional[str] = Field(None, description="串口名称，为空时使用默认串口")
    delay: Optional[float] = Field(0, description="发送后延迟时间(秒)")


class ExpectStep(WorkflowStepBase):
    """期望回复步骤"""
    type: StepType = Field(StepType.EXPECT, description="步骤类型")
    expect_type: ExpectType = Field(..., description="期望匹配类型")
    pattern: str = Field(..., description="期望的字符串或正则表达式")
    timeout: Optional[float] = Field(10.0, description="超时时间(秒)")
    on_timeout: Optional[str] = Field(None, description="超时时的处理逻辑")


class AssignStep(WorkflowStepBase):
    """变量赋值步骤"""
    type: StepType = Field(StepType.ASSIGN, description="步骤类型")
    variable: str = Field(..., description="变量名")
    expression: str = Field(..., description="赋值表达式，支持正则提取和逻辑运算")


class ConfirmStep(WorkflowStepBase):
    """确认步骤"""
    type: StepType = Field(StepType.CONFIRM, description="步骤类型")
    message: str = Field(..., description="确认消息")
    options: List[str] = Field(default=["确认", "取消"], description="可选操作")
    timeout: Optional[float] = Field(None, description="超时时间(秒)，为空时无限等待")


class ControlStep(WorkflowStepBase):
    """控制步骤"""
    type: StepType = Field(StepType.CONTROL, description="步骤类型")
    control_type: ControlType = Field(..., description="控制类型")
    condition: Optional[str] = Field(None, description="条件表达式（if/loop时必需）")
    steps: Optional[List["WorkflowStep"]] = Field(None, description="子步骤列表")


# 联合类型，支持所有步骤类型
WorkflowStep = Union[SendStep, ExpectStep, AssignStep, ConfirmStep, ControlStep]


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    id: Optional[str] = Field(None, description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: str = Field("1.0", description="版本号")
    variables: Dict[str, Any] = Field(default_factory=dict, description="初始变量")
    steps: List[WorkflowStep] = Field(..., description="工作流步骤")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class WorkflowExecutionStatus(str, Enum):
    """工作流执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowExecution(BaseModel):
    """工作流执行实例"""
    id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    status: WorkflowExecutionStatus = Field(..., description="执行状态")
    current_step: Optional[str] = Field(None, description="当前执行步骤ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="当前变量上下文")
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="执行日志")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    variables: Dict[str, Any] = Field(default_factory=dict, description="初始变量")
    steps: List[Dict[str, Any]] = Field(..., description="工作流步骤定义")


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = Field(None, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    variables: Optional[Dict[str, Any]] = Field(None, description="初始变量")
    steps: Optional[List[Dict[str, Any]]] = Field(None, description="工作流步骤定义")


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    variables: Optional[Dict[str, Any]] = Field(None, description="执行时的变量覆盖")
    session_id: Optional[str] = Field(None, description="关联的会话ID")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str = Field(..., description="执行ID")
    status: WorkflowExecutionStatus = Field(..., description="执行状态")
    message: str = Field(..., description="响应消息")


class WorkflowConfirmRequest(BaseModel):
    """工作流确认请求"""
    execution_id: str = Field(..., description="执行ID")
    action: str = Field(..., description="用户选择的操作")


class WorkflowLog(BaseModel):
    """工作流日志条目"""
    timestamp: str = Field(..., description="时间戳")
    step_id: str = Field(..., description="步骤ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[WorkflowDefinition] = Field(..., description="工作流列表")
    total: int = Field(..., description="总数量")


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行列表响应"""
    executions: List[WorkflowExecution] = Field(..., description="执行列表")
    total: int = Field(..., description="总数量")


# 更新前向引用
ControlStep.model_rebuild()