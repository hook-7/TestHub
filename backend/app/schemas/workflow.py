"""
工作流自动化系统数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime


class StepType(str, Enum):
    """步骤类型"""
    SERIAL_SEND = "serial_send"      # 发送串口指令
    WAIT_RESPONSE = "wait_response"   # 等待串口回复
    USER_CONFIRM = "user_confirm"     # 用户确认
    SET_VARIABLE = "set_variable"     # 设置变量
    CONDITION = "condition"           # 条件判断
    DELAY = "delay"                   # 延时等待
    LOG = "log"                       # 记录日志


class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"           # 草稿
    READY = "ready"           # 就绪
    RUNNING = "running"       # 运行中
    PAUSED = "paused"         # 暂停
    COMPLETED = "completed"   # 完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 取消


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    SKIPPED = "skipped"       # 跳过
    WAITING = "waiting"       # 等待用户操作


class WorkflowStep(BaseModel):
    """工作流步骤"""
    step_id: str = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    step_type: StepType = Field(..., description="步骤类型")
    description: Optional[str] = Field(None, description="步骤描述")
    
    # 串口相关配置
    serial_command: Optional[str] = Field(None, description="串口发送指令，支持变量 ${var}")
    expected_response: Optional[str] = Field(None, description="期望的串口回复，支持正则表达式")
    response_timeout: Optional[int] = Field(default=5, description="回复超时时间(秒)")
    
    # 用户确认配置
    confirm_message: Optional[str] = Field(None, description="确认消息内容")
    confirm_options: Optional[List[str]] = Field(None, description="确认选项")
    
    # 变量操作
    variable_name: Optional[str] = Field(None, description="变量名")
    variable_value: Optional[str] = Field(None, description="变量值，支持表达式")
    variable_source: Optional[str] = Field(None, description="变量来源：response/user_input/fixed")
    
    # 条件判断
    condition_expression: Optional[str] = Field(None, description="条件表达式")
    true_next_step: Optional[str] = Field(None, description="条件为真时的下一步骤ID")
    false_next_step: Optional[str] = Field(None, description="条件为假时的下一步骤ID")
    
    # 通用配置
    delay_seconds: Optional[int] = Field(None, description="延时秒数")
    retry_count: Optional[int] = Field(default=0, description="重试次数")
    next_step_id: Optional[str] = Field(None, description="下一步骤ID")
    
    # 执行状态
    status: StepStatus = Field(default=StepStatus.PENDING, description="执行状态")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    executed_at: Optional[datetime] = Field(None, description="执行时间")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: str = Field(default="1.0", description="版本号")
    
    # 步骤定义
    steps: List[WorkflowStep] = Field(..., description="工作流步骤列表")
    start_step_id: str = Field(..., description="起始步骤ID")
    
    # 变量定义
    variables: Dict[str, Any] = Field(default_factory=dict, description="工作流变量")
    
    # 配置
    timeout_seconds: Optional[int] = Field(default=300, description="整体超时时间")
    auto_save_results: bool = Field(default=True, description="是否自动保存结果")
    
    # 元数据
    created_by: Optional[str] = Field(None, description="创建者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class WorkflowExecution(BaseModel):
    """工作流执行实例"""
    execution_id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    
    # 执行状态
    status: WorkflowStatus = Field(default=WorkflowStatus.READY, description="执行状态")
    current_step_id: Optional[str] = Field(None, description="当前步骤ID")
    
    # 执行数据
    variables: Dict[str, Any] = Field(default_factory=dict, description="运行时变量")
    step_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="步骤执行结果")
    
    # 执行信息
    started_by: Optional[str] = Field(None, description="执行者")
    workstation_id: Optional[str] = Field(None, description="工位ID")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    failed_step_id: Optional[str] = Field(None, description="失败步骤ID")


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    workflow_id: str = Field(..., description="工作流ID")
    input_variables: Dict[str, Any] = Field(default_factory=dict, description="输入变量")
    operator_id: Optional[str] = Field(None, description="操作员ID")
    workstation_id: Optional[str] = Field(None, description="工位ID")


class UserConfirmationRequest(BaseModel):
    """用户确认请求"""
    execution_id: str = Field(..., description="执行ID")
    step_id: str = Field(..., description="步骤ID")
    confirmed: bool = Field(..., description="是否确认")
    user_input: Optional[str] = Field(None, description="用户输入")
    selected_option: Optional[str] = Field(None, description="选择的选项")
    operator_notes: Optional[str] = Field(None, description="操作员备注")


class WorkflowStepResult(BaseModel):
    """工作流步骤结果"""
    step_id: str = Field(..., description="步骤ID")
    status: StepStatus = Field(..., description="执行状态")
    input_data: Optional[str] = Field(None, description="输入数据")
    output_data: Optional[str] = Field(None, description="输出数据")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    retry_count: int = Field(default=0, description="重试次数")
    error_message: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class WorkflowTemplate(BaseModel):
    """工作流模板"""
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    category: str = Field(..., description="分类")
    description: str = Field(..., description="模板描述")
    workflow_definition: WorkflowDefinition = Field(..., description="工作流定义")
    is_active: bool = Field(default=True, description="是否启用")
    usage_count: int = Field(default=0, description="使用次数")


class WebSocketMessage(BaseModel):
    """WebSocket消息"""
    message_type: str = Field(..., description="消息类型")
    execution_id: str = Field(..., description="执行ID")
    step_id: Optional[str] = Field(None, description="步骤ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")