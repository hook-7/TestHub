"""
Workflow Service
工作流编排服务
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.workflow_schemas import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionLog,
    WorkflowExecutionResult,
    WorkflowStats,
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowStatus,
    WorkflowNodeStatus,
    WorkflowNodeType
)
from app.services.command_service import command_service

logger = logging.getLogger(__name__)


class WorkflowService:
    """工作流服务"""
    
    def __init__(self):
        # 内存存储，实际项目中应该使用数据库
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._next_workflow_id = 1
        self._next_execution_id = 1
    
    async def get_all_workflows(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取所有工作流"""
        try:
            workflows = list(self._workflows.values())
            
            # 状态过滤
            if status:
                workflows = [w for w in workflows if w.status.value == status]
            
            # 搜索过滤
            if search:
                search_lower = search.lower()
                workflows = [
                    w for w in workflows 
                    if search_lower in w.name.lower() or 
                       (w.description and search_lower in w.description.lower())
                ]
            
            # 分页
            total = len(workflows)
            start = (page - 1) * page_size
            end = start + page_size
            workflows = workflows[start:end]
            
            return {
                "workflows": workflows,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流详情"""
        try:
            return self._workflows.get(workflow_id)
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {e}")
            raise
    
    async def create_workflow(self, request: CreateWorkflowRequest) -> WorkflowDefinition:
        """创建工作流"""
        try:
            workflow_id = f"wf_{self._next_workflow_id:06d}"
            self._next_workflow_id += 1
            
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=request.name,
                description=request.description,
                nodes=request.nodes,
                connections=request.connections,
                variables=request.variables,
                settings=request.settings or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self._workflows[workflow_id] = workflow
            logger.info(f"Created workflow {workflow_id}: {workflow.name}")
            return workflow
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise
    
    async def update_workflow(self, workflow_id: str, request: UpdateWorkflowRequest) -> Optional[WorkflowDefinition]:
        """更新工作流"""
        try:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                return None
            
            # 更新字段
            if request.name is not None:
                workflow.name = request.name
            if request.description is not None:
                workflow.description = request.description
            if request.nodes is not None:
                workflow.nodes = request.nodes
            if request.connections is not None:
                workflow.connections = request.connections
            if request.variables is not None:
                workflow.variables = request.variables
            if request.settings is not None:
                workflow.settings = request.settings
            if request.status is not None:
                workflow.status = request.status
            
            workflow.updated_at = datetime.now()
            
            logger.info(f"Updated workflow {workflow_id}: {workflow.name}")
            return workflow
        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {e}")
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        try:
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
                logger.info(f"Deleted workflow {workflow_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            raise
    
    async def duplicate_workflow(self, workflow_id: str, new_name: str) -> Optional[WorkflowDefinition]:
        """复制工作流"""
        try:
            original = self._workflows.get(workflow_id)
            if not original:
                return None
            
            new_id = f"wf_{self._next_workflow_id:06d}"
            self._next_workflow_id += 1
            
            # 复制节点和连接，生成新的ID
            new_nodes = []
            node_id_mapping = {}
            
            for node in original.nodes:
                new_node_id = f"node_{uuid.uuid4().hex[:8]}"
                node_id_mapping[node.id] = new_node_id
                
                new_node = node.model_copy()
                new_node.id = new_node_id
                new_node.created_at = datetime.now()
                new_node.updated_at = datetime.now()
                new_nodes.append(new_node)
            
            new_connections = []
            for connection in original.connections:
                new_connection_id = f"conn_{uuid.uuid4().hex[:8]}"
                new_connection = connection.model_copy()
                new_connection.id = new_connection_id
                new_connection.source_node_id = node_id_mapping.get(connection.source_node_id, connection.source_node_id)
                new_connection.target_node_id = node_id_mapping.get(connection.target_node_id, connection.target_node_id)
                new_connection.created_at = datetime.now()
                new_connections.append(new_connection)
            
            workflow = WorkflowDefinition(
                id=new_id,
                name=new_name,
                description=original.description,
                nodes=new_nodes,
                connections=new_connections,
                variables=original.variables.copy() if original.variables else [],
                settings=original.settings.model_copy() if original.settings else {},
                status=WorkflowStatus.DRAFT,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by=original.created_by
            )
            
            self._workflows[new_id] = workflow
            logger.info(f"Duplicated workflow {workflow_id} to {new_id}: {new_name}")
            return workflow
        except Exception as e:
            logger.error(f"Error duplicating workflow {workflow_id}: {e}")
            raise
    
    async def execute_workflow(self, request: ExecuteWorkflowRequest) -> WorkflowExecution:
        """执行工作流"""
        try:
            workflow = self._workflows.get(request.workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {request.workflow_id} not found")
            
            execution_id = f"exec_{self._next_execution_id:06d}"
            self._next_execution_id += 1
            
            # 创建执行实例
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                status=WorkflowStatus.RUNNING,
                start_time=datetime.now(),
                variables=request.variables or {},
                logs=[],
                created_at=datetime.now()
            )
            
            # 添加执行变量
            if request.mac_address:
                execution.variables["mac_address"] = request.mac_address
            if request.serial_number:
                execution.variables["serial_number"] = request.serial_number
            if request.operator:
                execution.variables["operator"] = request.operator
            if request.workstation:
                execution.variables["workstation"] = request.workstation
            if request.device_id:
                execution.variables["device_id"] = request.device_id
            if request.input_data:
                execution.variables.update(request.input_data)
            
            self._executions[execution_id] = execution
            
            # 异步执行工作流
            # 这里应该启动一个后台任务来执行工作流
            # 为了简化，我们只是创建执行记录
            logger.info(f"Started execution {execution_id} for workflow {workflow.id}")
            
            return execution
        except Exception as e:
            logger.error(f"Error executing workflow {request.workflow_id}: {e}")
            raise
    
    async def get_executions(
        self,
        page: int = 1,
        page_size: int = 20,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取执行记录"""
        try:
            executions = list(self._executions.values())
            
            # 工作流过滤
            if workflow_id:
                executions = [e for e in executions if e.workflow_id == workflow_id]
            
            # 状态过滤
            if status:
                executions = [e for e in executions if e.status.value == status]
            
            # 按创建时间倒序排列
            executions.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            total = len(executions)
            start = (page - 1) * page_size
            end = start + page_size
            executions = executions[start:end]
            
            return {
                "executions": executions,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"Error getting executions: {e}")
            raise
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行详情"""
        try:
            return self._executions.get(execution_id)
        except Exception as e:
            logger.error(f"Error getting execution {execution_id}: {e}")
            raise
    
    async def stop_execution(self, execution_id: str) -> bool:
        """停止执行"""
        try:
            execution = self._executions.get(execution_id)
            if execution and execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.CANCELLED
                execution.end_time = datetime.now()
                logger.info(f"Stopped execution {execution_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping execution {execution_id}: {e}")
            raise
    
    async def get_stats(self) -> WorkflowStats:
        """获取统计信息"""
        try:
            workflows = list(self._workflows.values())
            executions = list(self._executions.values())
            
            total_workflows = len(workflows)
            active_workflows = len([w for w in workflows if w.status == WorkflowStatus.ACTIVE])
            total_executions = len(executions)
            success_executions = len([e for e in executions if e.status == WorkflowStatus.COMPLETED])
            failed_executions = len([e for e in executions if e.status == WorkflowStatus.FAILED])
            
            # 计算平均执行时间
            completed_executions = [e for e in executions if e.end_time and e.status == WorkflowStatus.COMPLETED]
            if completed_executions:
                total_duration = sum(
                    int((e.end_time - e.start_time).total_seconds() * 1000)
                    for e in completed_executions
                )
                average_execution_time = total_duration / len(completed_executions)
            else:
                average_execution_time = 0.0
            
            return WorkflowStats(
                total_workflows=total_workflows,
                active_workflows=active_workflows,
                total_executions=total_executions,
                success_executions=success_executions,
                failed_executions=failed_executions,
                average_execution_time=average_execution_time
            )
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise


# 创建服务实例
workflow_service = WorkflowService()