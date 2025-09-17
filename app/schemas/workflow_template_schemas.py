"""
Workflow Template Schemas
工作流模板相关的数据模型 - 基于Command对象的简单模板系统
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from enum import Enum


class WorkflowTemplateStatus(str, Enum):
    """工作流模板状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class WorkflowStep(BaseModel):
    """工作流步骤 - 基于Command对象"""
    step_id: str = Field(..., description="步骤ID")
    step_name: str = Field(..., description="步骤名称")
    command_id: str = Field(..., description="关联的命令ID")
    command_name: str = Field(..., description="命令名称")
    command: str = Field(..., description="命令内容")
    expected_response: str = Field(default="", description="期望响应")
    timeout: int = Field(default=5000, description="超时时间(ms)")
    retry_count: int = Field(default=0, description="重试次数")
    delay_before: int = Field(default=0, description="执行前延迟(ms)")
    delay_after: int = Field(default=0, description="执行后延迟(ms)")
    required: bool = Field(default=True, description="是否必需步骤")
    description: str = Field(default="", description="步骤描述")
    order: int = Field(..., description="执行顺序")


class WorkflowTemplate(BaseModel):
    """工作流模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(default="", description="模板描述")
    category: str = Field(default="default", description="模板分类")
    version: str = Field(default="1.0.0", description="模板版本")
    status: WorkflowTemplateStatus = Field(default=WorkflowTemplateStatus.DRAFT, description="模板状态")
    steps: List[WorkflowStep] = Field(default=[], description="工作流步骤")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: str = Field(default="system", description="创建者")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)


class WorkflowExecution(BaseModel):
    """工作流执行实例"""
    id: str = Field(..., description="执行ID")
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    status: str = Field(default="pending", description="执行状态")
    mac_address: str = Field(..., description="MAC地址")
    serial_number: str = Field(..., description="序列号")
    operator: str = Field(..., description="操作员")
    workstation: str = Field(..., description="工位")
    device_id: str = Field(..., description="设备ID")
    input_data: Dict[str, Any] = Field(default={}, description="输入数据")
    current_step: int = Field(default=0, description="当前步骤")
    total_steps: int = Field(default=0, description="总步骤数")
    progress: float = Field(default=0.0, description="执行进度(0-100)")
    step_results: List[Dict[str, Any]] = Field(default=[], description="步骤执行结果")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)


class CreateWorkflowTemplateRequest(BaseModel):
    """创建工作流模板请求"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: str = Field(default="", max_length=500, description="模板描述")
    category: str = Field(default="default", max_length=50, description="模板分类")
    command_ids: List[str] = Field(..., min_items=1, description="命令ID列表")


class UpdateWorkflowTemplateRequest(BaseModel):
    """更新工作流模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    status: Optional[WorkflowTemplateStatus] = Field(None, description="模板状态")
    command_ids: Optional[List[str]] = Field(None, min_items=1, description="命令ID列表")


class ExecuteWorkflowRequest(BaseModel):
    """执行工作流请求"""
    template_id: str = Field(..., description="模板ID")
    mac_address: str = Field(..., min_length=1, description="MAC地址")
    serial_number: str = Field(..., min_length=1, description="序列号")
    operator: str = Field(..., min_length=1, description="操作员")
    workstation: str = Field(..., min_length=1, description="工位")
    device_id: str = Field(..., min_length=1, description="设备ID")
    input_data: Dict[str, Any] = Field(default={}, description="输入数据")


class WorkflowTemplateListResponse(BaseModel):
    """工作流模板列表响应"""
    templates: List[WorkflowTemplate] = Field(default=[], description="模板列表")
    total: int = Field(default=0, description="模板总数")


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行列表响应"""
    executions: List[WorkflowExecution] = Field(default=[], description="执行列表")
    total: int = Field(default=0, description="执行总数")


class WorkflowStats(BaseModel):
    """工作流统计信息"""
    total_templates: int = Field(default=0, description="模板总数")
    active_templates: int = Field(default=0, description="活跃模板数")
    total_executions: int = Field(default=0, description="执行总数")
    successful_executions: int = Field(default=0, description="成功执行数")
    failed_executions: int = Field(default=0, description="失败执行数")
    running_executions: int = Field(default=0, description="正在执行数")
    success_rate: float = Field(default=0.0, description="成功率")