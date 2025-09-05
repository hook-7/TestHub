"""
Workflow Schemas
批量作业工作流相关的数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class WorkflowStepCreate(BaseModel):
    """创建工作流步骤请求模型"""
    command_id: str = Field(..., description="关联的指令ID")
    step_order: int = Field(..., ge=1, description="执行顺序")
    delay_ms: int = Field(default=1000, ge=0, description="执行后延迟时间(毫秒)")
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    timeout_ms: int = Field(default=5000, ge=100, description="超时时间(毫秒)")


class WorkflowStep(BaseModel):
    """工作流步骤模型"""
    id: str = Field(..., description="步骤ID")
    workflow_id: str = Field(..., description="所属工作流ID")
    command_id: str = Field(..., description="关联的指令ID")
    step_order: int = Field(..., description="执行顺序")
    delay_ms: int = Field(..., description="执行后延迟时间(毫秒)")
    retry_count: int = Field(..., description="重试次数")
    timeout_ms: int = Field(..., description="超时时间(毫秒)")
    created_at: datetime = Field(..., description="创建时间")
    
    # 关联的指令信息
    command_name: Optional[str] = Field(None, description="指令名称")
    command_content: Optional[str] = Field(None, description="指令内容")
    command_description: Optional[str] = Field(None, description="指令描述")
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)
    
    model_config = {
        "from_attributes": True
    }


class CreateWorkflowRequest(BaseModel):
    """创建工作流请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    description: str = Field(default="", max_length=500, description="工作流描述")
    steps: List[WorkflowStepCreate] = Field(..., min_length=1, description="工作流步骤")


class UpdateWorkflowRequest(BaseModel):
    """更新工作流请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, max_length=500, description="工作流描述")
    steps: Optional[List[WorkflowStepCreate]] = Field(None, description="工作流步骤")


class BatchWorkflow(BaseModel):
    """批量工作流模型"""
    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    created_at: datetime = Field(..., description="创建时间")
    steps: List[WorkflowStep] = Field(default=[], description="工作流步骤")
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)
    
    model_config = {
        "from_attributes": True
    }


class WorkflowsListResponse(BaseModel):
    """工作流列表响应模型"""
    workflows: List[BatchWorkflow] = Field(default=[], description="工作流列表")
    total: int = Field(default=0, description="工作流总数")


class StepExecutionStatus(BaseModel):
    """步骤执行状态模型"""
    id: str = Field(..., description="步骤执行ID")
    step_id: str = Field(..., description="步骤ID")
    status: str = Field(..., description="执行状态")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    finished_at: Optional[datetime] = Field(None, description="结束时间")
    command_sent: Optional[str] = Field(None, description="发送的指令")
    response_received: Optional[str] = Field(None, description="接收的响应")
    retry_attempt: int = Field(..., description="重试次数")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    
    # 关联的步骤信息
    step_order: Optional[int] = Field(None, description="步骤顺序")
    command_name: Optional[str] = Field(None, description="指令名称")
    command_content: Optional[str] = Field(None, description="指令内容")
    
    @field_serializer('started_at', 'finished_at', 'created_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000) if dt else None
    
    model_config = {
        "from_attributes": True
    }


class WorkflowExecutionStatus(BaseModel):
    """工作流执行状态模型"""
    id: str = Field(..., description="执行记录ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: Optional[str] = Field(None, description="工作流名称")
    status: str = Field(..., description="执行状态")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    finished_at: Optional[datetime] = Field(None, description="结束时间")
    total_steps: int = Field(..., description="总步骤数")
    completed_steps: int = Field(..., description="已完成步骤数")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    steps: List[StepExecutionStatus] = Field(default=[], description="步骤执行状态")
    
    @field_serializer('started_at', 'finished_at', 'created_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000) if dt else None
    
    model_config = {
        "from_attributes": True
    }


class ExecuteWorkflowRequest(BaseModel):
    """执行工作流请求模型"""
    workflow_id: str = Field(..., description="要执行的工作流ID")


class ExecuteWorkflowResponse(BaseModel):
    """执行工作流响应模型"""
    execution_id: str = Field(..., description="执行记录ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: str = Field(..., description="执行状态")
    total_steps: int = Field(..., description="总步骤数")