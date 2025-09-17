"""
Workflow Schemas
工作流编排相关的数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from enum import Enum


class WorkflowNodeType(str, Enum):
    """工作流节点类型"""
    START = "start"
    END = "end"
    COMMAND = "command"
    WORKFLOW = "workflow"
    CONDITION = "condition"
    DELAY = "delay"
    NOTIFICATION = "notification"


class WorkflowNodeStatus(str, Enum):
    """工作流节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowNodeConfig(BaseModel):
    """工作流节点配置"""
    # 命令节点配置
    command_id: Optional[str] = Field(None, description="关联的命令ID")
    command: Optional[str] = Field(None, description="直接命令内容")
    expected_response: Optional[str] = Field(None, description="期望响应")
    timeout: Optional[int] = Field(None, description="超时时间(ms)")
    retry_count: Optional[int] = Field(None, description="重试次数")
    
    # 工作流引用节点配置
    workflow_id: Optional[str] = Field(None, description="引用的工作流ID")
    workflow_name: Optional[str] = Field(None, description="引用的工作流名称")
    input_variables: Optional[Dict[str, Any]] = Field(None, description="传递给子工作流的变量")
    
    # 条件节点配置
    condition: Optional[str] = Field(None, description="条件表达式")
    true_next: Optional[str] = Field(None, description="条件为真时的下一个节点ID")
    false_next: Optional[str] = Field(None, description="条件为假时的下一个节点ID")
    
    # 延迟节点配置
    delay_time: Optional[int] = Field(None, description="延迟时间(ms)")
    
    # 通知节点配置
    notification_title: Optional[str] = Field(None, description="通知标题")
    notification_message: Optional[str] = Field(None, description="通知内容")
    notification_type: Optional[str] = Field(None, description="通知类型")


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str = Field(..., description="节点ID")
    type: WorkflowNodeType = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    position: Dict[str, int] = Field(..., description="节点位置 {x, y}")
    status: WorkflowNodeStatus = Field(default=WorkflowNodeStatus.PENDING, description="节点状态")
    config: WorkflowNodeConfig = Field(default_factory=WorkflowNodeConfig, description="节点配置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)


class WorkflowConnection(BaseModel):
    """工作流连接"""
    id: str = Field(..., description="连接ID")
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    label: Optional[str] = Field(None, description="连接标签")
    condition: Optional[str] = Field(None, description="连接条件")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)


class WorkflowVariable(BaseModel):
    """工作流变量"""
    id: str = Field(..., description="变量ID")
    name: str = Field(..., description="变量名称")
    type: str = Field(..., description="变量类型")
    value: Any = Field(..., description="变量值")
    description: Optional[str] = Field(None, description="变量描述")
    is_required: bool = Field(default=False, description="是否必需")


class WorkflowSettings(BaseModel):
    """工作流设置"""
    auto_start: bool = Field(default=False, description="自动开始")
    max_execution_time: int = Field(default=300000, description="最大执行时间(ms)")
    retry_on_failure: bool = Field(default=True, description="失败时重试")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout: int = Field(default=30000, description="全局超时时间(ms)")
    require_mac_address: bool = Field(default=True, description="是否需要MAC地址")
    require_serial_number: bool = Field(default=False, description="是否需要SN序列号")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: str = Field(default="1.0.0", description="版本号")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="工作流状态")
    nodes: List[WorkflowNode] = Field(default=[], description="节点列表")
    connections: List[WorkflowConnection] = Field(default=[], description="连接列表")
    variables: List[WorkflowVariable] = Field(default=[], description="变量列表")
    settings: WorkflowSettings = Field(default_factory=WorkflowSettings, description="工作流设置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)


class WorkflowExecutionLog(BaseModel):
    """工作流执行日志"""
    id: str = Field(..., description="日志ID")
    node_id: str = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    node_type: WorkflowNodeType = Field(..., description="节点类型")
    status: WorkflowNodeStatus = Field(..., description="节点状态")
    message: str = Field(..., description="日志消息")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    duration: Optional[int] = Field(None, description="执行时长(ms)")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime) -> int:
        """将datetime序列化为毫秒时间戳"""
        return int(dt.timestamp() * 1000)


class WorkflowExecutionResult(BaseModel):
    """工作流执行结果"""
    success: bool = Field(..., description="是否成功")
    total_nodes: int = Field(..., description="总节点数")
    executed_nodes: int = Field(..., description="已执行节点数")
    success_nodes: int = Field(..., description="成功节点数")
    failed_nodes: int = Field(..., description="失败节点数")
    skipped_nodes: int = Field(..., description="跳过节点数")
    duration: int = Field(..., description="总执行时长(ms)")
    variables: Dict[str, Any] = Field(default={}, description="执行变量")


class WorkflowExecution(BaseModel):
    """工作流执行实例"""
    id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: WorkflowStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    current_node_id: Optional[str] = Field(None, description="当前节点ID")
    variables: Dict[str, Any] = Field(default={}, description="执行变量")
    logs: List[WorkflowExecutionLog] = Field(default=[], description="执行日志")
    result: Optional[WorkflowExecutionResult] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)


# 请求模型
class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, max_length=500, description="工作流描述")
    nodes: List[WorkflowNode] = Field(default=[], description="节点列表")
    connections: List[WorkflowConnection] = Field(default=[], description="连接列表")
    variables: List[WorkflowVariable] = Field(default=[], description="变量列表")
    settings: Optional[WorkflowSettings] = Field(None, description="工作流设置")


class UpdateWorkflowRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, max_length=500, description="工作流描述")
    nodes: Optional[List[WorkflowNode]] = Field(None, description="节点列表")
    connections: Optional[List[WorkflowConnection]] = Field(None, description="连接列表")
    variables: Optional[List[WorkflowVariable]] = Field(None, description="变量列表")
    settings: Optional[WorkflowSettings] = Field(None, description="工作流设置")
    status: Optional[WorkflowStatus] = Field(None, description="工作流状态")


class ExecuteWorkflowRequest(BaseModel):
    """执行工作流请求"""
    workflow_id: str = Field(..., description="工作流ID")
    variables: Optional[Dict[str, Any]] = Field(None, description="执行变量")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    serial_number: Optional[str] = Field(None, description="SN序列号")
    operator: Optional[str] = Field(None, description="操作员")
    workstation: Optional[str] = Field(None, description="工位")
    device_id: Optional[str] = Field(None, description="设备ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="其他输入数据")


# 响应模型
class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[WorkflowDefinition] = Field(..., description="工作流列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行列表响应"""
    executions: List[WorkflowExecution] = Field(..., description="执行列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class WorkflowStats(BaseModel):
    """工作流统计"""
    total_workflows: int = Field(..., description="总工作流数")
    active_workflows: int = Field(..., description="激活工作流数")
    total_executions: int = Field(..., description="总执行数")
    success_executions: int = Field(..., description="成功执行数")
    failed_executions: int = Field(..., description="失败执行数")
    average_execution_time: float = Field(..., description="平均执行时间(ms)")