"""
Workflow Template Service
工作流模板管理服务 - 基于Command对象的简单模板系统
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, and_, or_

from app.core.database import engine, Command
from app.core.config import settings
from app.schemas.workflow_template_schemas import (
    WorkflowTemplate, WorkflowStep, WorkflowExecution, 
    CreateWorkflowTemplateRequest, UpdateWorkflowTemplateRequest,
    ExecuteWorkflowRequest, WorkflowTemplateStatus, WorkflowStats
)
from app.services.command_service import command_service

logger = logging.getLogger(__name__)


class WorkflowTemplateService:
    """工作流模板管理服务"""

    def __init__(self):
        # 使用内存存储，实际项目中应该使用数据库
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        logger.info("Workflow template service initialized with memory storage")

    async def get_all_templates(self) -> List[WorkflowTemplate]:
        """获取所有工作流模板"""
        try:
            templates = list(self.templates.values())
            # 按创建时间倒序排序
            templates.sort(key=lambda x: x.created_at, reverse=True)
            logger.debug(f"Loaded {len(templates)} workflow templates")
            return templates
        except Exception as e:
            logger.error(f"Error getting all templates: {e}")
            return []

    async def get_template_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """根据ID获取工作流模板"""
        try:
            return self.templates.get(template_id)
        except Exception as e:
            logger.error(f"Error getting template by id {template_id}: {e}")
            return None

    async def create_template(self, request: CreateWorkflowTemplateRequest) -> Optional[WorkflowTemplate]:
        """创建工作流模板"""
        try:
            # 获取命令信息
            all_commands = await command_service.get_all_commands()
            command_map = {cmd.id: cmd for cmd in all_commands}
            
            # 验证命令ID
            steps = []
            for i, command_id in enumerate(request.command_ids):
                if command_id not in command_map:
                    logger.error(f"Command {command_id} not found")
                    return None
                
                cmd = command_map[command_id]
                step = WorkflowStep(
                    step_id=f"step_{i+1}",
                    step_name=f"步骤 {i+1}: {cmd.name}",
                    command_id=cmd.id,
                    command_name=cmd.name,
                    command=cmd.command,
                    expected_response=cmd.expected_response,
                    timeout=5000,
                    retry_count=0,
                    delay_before=0,
                    delay_after=0,
                    required=True,
                    description=cmd.description,
                    order=i + 1
                )
                steps.append(step)

            # 创建模板
            template_id = f"template_{uuid.uuid4().hex[:8]}"
            template = WorkflowTemplate(
                id=template_id,
                name=request.name,
                description=request.description,
                category=request.category,
                version="1.0.0",
                status=WorkflowTemplateStatus.ACTIVE,
                steps=steps,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by="system"
            )

            self.templates[template_id] = template
            logger.info(f"Created workflow template: {template.name} with {len(steps)} steps")
            return template

        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None

    async def update_template(self, template_id: str, request: UpdateWorkflowTemplateRequest) -> Optional[WorkflowTemplate]:
        """更新工作流模板"""
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.warning(f"Template {template_id} not found")
                return None

            # 更新基本信息
            if request.name is not None:
                template.name = request.name
            if request.description is not None:
                template.description = request.description
            if request.category is not None:
                template.category = request.category
            if request.status is not None:
                template.status = request.status

            # 更新步骤
            if request.command_ids is not None:
                all_commands = await command_service.get_all_commands()
                command_map = {cmd.id: cmd for cmd in all_commands}
                
                steps = []
                for i, command_id in enumerate(request.command_ids):
                    if command_id not in command_map:
                        logger.error(f"Command {command_id} not found")
                        return None
                    
                    cmd = command_map[command_id]
                    step = WorkflowStep(
                        step_id=f"step_{i+1}",
                        step_name=f"步骤 {i+1}: {cmd.name}",
                        command_id=cmd.id,
                        command_name=cmd.name,
                        command=cmd.command,
                        expected_response=cmd.expected_response,
                        timeout=5000,
                        retry_count=0,
                        delay_before=0,
                        delay_after=0,
                        required=True,
                        description=cmd.description,
                        order=i + 1
                    )
                    steps.append(step)
                
                template.steps = steps

            template.updated_at = datetime.now()
            self.templates[template_id] = template
            
            logger.info(f"Updated workflow template: {template.name}")
            return template

        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            return None

    async def delete_template(self, template_id: str) -> bool:
        """删除工作流模板"""
        try:
            if template_id in self.templates:
                del self.templates[template_id]
                logger.info(f"Deleted template: {template_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False

    async def execute_workflow(self, request: ExecuteWorkflowRequest) -> Optional[WorkflowExecution]:
        """执行工作流"""
        try:
            template = self.templates.get(request.template_id)
            if not template:
                logger.error(f"Template {request.template_id} not found")
                return None

            # 创建执行实例
            execution_id = f"exec_{uuid.uuid4().hex[:8]}"
            execution = WorkflowExecution(
                id=execution_id,
                template_id=request.template_id,
                template_name=template.name,
                status="pending",
                mac_address=request.mac_address,
                serial_number=request.serial_number,
                operator=request.operator,
                workstation=request.workstation,
                device_id=request.device_id,
                input_data=request.input_data,
                current_step=0,
                total_steps=len(template.steps),
                progress=0.0,
                step_results=[],
                created_at=datetime.now()
            )

            self.executions[execution_id] = execution
            
            # 异步执行工作流
            import asyncio
            asyncio.create_task(self._execute_workflow_steps(execution_id))
            
            logger.info(f"Started workflow execution: {execution_id} for template: {template.name}")
            return execution

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return None

    async def _execute_workflow_steps(self, execution_id: str):
        """执行工作流步骤"""
        try:
            execution = self.executions.get(execution_id)
            if not execution:
                return

            execution.status = "running"
            execution.start_time = datetime.now()

            template = self.templates.get(execution.template_id)
            if not template:
                execution.status = "failed"
                execution.error_message = "Template not found"
                execution.end_time = datetime.now()
                return

            # 执行每个步骤
            for i, step in enumerate(template.steps):
                execution.current_step = i + 1
                execution.progress = (i / len(template.steps)) * 100

                # 执行前延迟
                if step.delay_before > 0:
                    import asyncio
                    await asyncio.sleep(step.delay_before / 1000.0)

                # 执行命令（这里模拟执行）
                step_result = {
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "command": step.command,
                    "status": "success",
                    "response": f"模拟响应: {step.expected_response}",
                    "execution_time": datetime.now().isoformat(),
                    "duration_ms": 1000
                }

                execution.step_results.append(step_result)

                # 执行后延迟
                if step.delay_after > 0:
                    import asyncio
                    await asyncio.sleep(step.delay_after / 1000.0)

            # 完成执行
            execution.status = "completed"
            execution.progress = 100.0
            execution.end_time = datetime.now()
            
            logger.info(f"Completed workflow execution: {execution_id}")

        except Exception as e:
            logger.error(f"Error executing workflow steps for {execution_id}: {e}")
            execution = self.executions.get(execution_id)
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.end_time = datetime.now()

    async def get_execution_by_id(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行实例"""
        return self.executions.get(execution_id)

    async def get_all_executions(self) -> List[WorkflowExecution]:
        """获取所有执行实例"""
        executions = list(self.executions.values())
        executions.sort(key=lambda x: x.created_at, reverse=True)
        return executions

    async def stop_execution(self, execution_id: str) -> bool:
        """停止执行"""
        try:
            execution = self.executions.get(execution_id)
            if execution and execution.status == "running":
                execution.status = "cancelled"
                execution.end_time = datetime.now()
                logger.info(f"Stopped execution: {execution_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping execution {execution_id}: {e}")
            return False

    async def get_stats(self) -> WorkflowStats:
        """获取统计信息"""
        try:
            templates = list(self.templates.values())
            executions = list(self.executions.values())
            
            active_templates = len([t for t in templates if t.status == WorkflowTemplateStatus.ACTIVE])
            successful_executions = len([e for e in executions if e.status == "completed"])
            failed_executions = len([e for e in executions if e.status == "failed"])
            running_executions = len([e for e in executions if e.status == "running"])
            
            total_executions = len(executions)
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0

            stats = WorkflowStats(
                total_templates=len(templates),
                active_templates=active_templates,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                running_executions=running_executions,
                success_rate=success_rate
            )

            logger.info(f"Generated workflow stats: {stats.total_templates} templates, {stats.total_executions} executions")
            return stats

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return WorkflowStats()


# 创建全局实例
workflow_template_service = WorkflowTemplateService()