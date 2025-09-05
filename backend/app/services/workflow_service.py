"""
Workflow Service
批量作业工作流管理服务
"""

import logging
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, and_, or_

from app.core.database import (
    engine, 
    Command, 
    BatchWorkflow, 
    WorkflowStep, 
    WorkflowExecution, 
    StepExecution
)
from app.schemas.workflow_schemas import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    BatchWorkflow as WorkflowSchema,
    WorkflowStep as WorkflowStepSchema,
    WorkflowExecutionStatus,
    StepExecutionStatus,
    ExecuteWorkflowResponse
)
from app.services.serial_service import serial_service

logger = logging.getLogger(__name__)


class WorkflowService:
    """批量作业工作流管理服务"""

    def __init__(self):
        logger.info("Workflow service initialized")
        self._running_executions: Dict[str, bool] = {}  # 跟踪正在运行的执行

    def _get_session(self):
        """获取数据库会话"""
        return Session(engine)

    async def get_all_workflows(self) -> List[WorkflowSchema]:
        """获取所有工作流"""
        try:
            with self._get_session() as session:
                # 查询所有工作流
                db_workflows = session.exec(
                    select(BatchWorkflow).order_by(BatchWorkflow.created_at.desc())
                ).all()

                workflows = []
                for workflow in db_workflows:
                    # 获取工作流的步骤
                    steps = await self._get_workflow_steps_with_commands(session, workflow.id)
                    
                    workflow_schema = WorkflowSchema(
                        id=workflow.id,
                        name=workflow.name,
                        description=workflow.description,
                        created_at=workflow.created_at,
                        steps=steps
                    )
                    workflows.append(workflow_schema)

                logger.debug(f"Loaded {len(workflows)} workflows from database")
                return workflows
        except Exception as e:
            logger.error(f"Error getting all workflows: {e}")
            return []

    async def _get_workflow_steps_with_commands(self, session: Session, workflow_id: str) -> List[WorkflowStepSchema]:
        """获取工作流步骤及关联的指令信息"""
        try:
            # 联查步骤和指令信息
            query = (
                select(WorkflowStep, Command)
                .join(Command, WorkflowStep.command_id == Command.id)
                .where(WorkflowStep.workflow_id == workflow_id)
                .order_by(WorkflowStep.step_order)
            )
            
            results = session.exec(query).all()
            
            steps = []
            for step, command in results:
                step_schema = WorkflowStepSchema(
                    id=step.id,
                    workflow_id=step.workflow_id,
                    command_id=step.command_id,
                    step_order=step.step_order,
                    delay_ms=step.delay_ms,
                    retry_count=step.retry_count,
                    timeout_ms=step.timeout_ms,
                    created_at=step.created_at,
                    command_name=command.name,
                    command_content=command.command,
                    command_description=command.description
                )
                # 添加期望响应作为动态属性
                step_schema.command_expected_response = command.expected_response
                steps.append(step_schema)
            
            return steps
        except Exception as e:
            logger.error(f"Error getting workflow steps: {e}")
            return []

    async def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowSchema]:
        """根据ID获取工作流"""
        try:
            with self._get_session() as session:
                db_workflow = session.exec(
                    select(BatchWorkflow).where(BatchWorkflow.id == workflow_id)
                ).first()

                if not db_workflow:
                    return None

                # 获取工作流的步骤
                steps = await self._get_workflow_steps_with_commands(session, workflow_id)
                
                return WorkflowSchema(
                    id=db_workflow.id,
                    name=db_workflow.name,
                    description=db_workflow.description,
                    created_at=db_workflow.created_at,
                    steps=steps
                )
        except Exception as e:
            logger.error(f"Error getting workflow by id {workflow_id}: {e}")
            return None

    async def create_workflow(self, request: CreateWorkflowRequest) -> Optional[WorkflowSchema]:
        """创建新工作流"""
        try:
            with self._get_session() as session:
                # 检查是否已存在相同名称的工作流
                existing = session.exec(
                    select(BatchWorkflow).where(BatchWorkflow.name.ilike(request.name.strip()))
                ).first()

                if existing:
                    logger.warning(f"Workflow with name '{request.name}' already exists")
                    return None

                # 验证所有指令ID是否存在
                command_ids = [step.command_id for step in request.steps]
                existing_commands = session.exec(
                    select(Command).where(Command.id.in_(command_ids))
                ).all()
                
                existing_command_ids = {cmd.id for cmd in existing_commands}
                missing_command_ids = set(command_ids) - existing_command_ids
                
                if missing_command_ids:
                    logger.warning(f"Commands not found: {missing_command_ids}")
                    return None

                # 创建工作流
                workflow_id = str(uuid.uuid4())
                new_workflow = BatchWorkflow(
                    id=workflow_id,
                    name=request.name.strip(),
                    description=request.description.strip()
                )

                session.add(new_workflow)

                # 创建工作流步骤
                for step_data in request.steps:
                    new_step = WorkflowStep(
                        id=str(uuid.uuid4()),
                        workflow_id=workflow_id,
                        command_id=step_data.command_id,
                        step_order=step_data.step_order,
                        delay_ms=step_data.delay_ms,
                        retry_count=step_data.retry_count,
                        timeout_ms=step_data.timeout_ms
                    )
                    session.add(new_step)

                session.commit()
                session.refresh(new_workflow)

                logger.info(f"Created new workflow: {new_workflow.name}")
                
                # 返回完整的工作流信息
                return await self.get_workflow_by_id(workflow_id)

        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None

    async def update_workflow(self, workflow_id: str, request: UpdateWorkflowRequest) -> Optional[WorkflowSchema]:
        """更新工作流"""
        try:
            with self._get_session() as session:
                # 查找要更新的工作流
                db_workflow = session.exec(
                    select(BatchWorkflow).where(BatchWorkflow.id == workflow_id)
                ).first()

                if not db_workflow:
                    logger.warning(f"Workflow with id {workflow_id} not found")
                    return None

                # 检查名称冲突（如果要更新名称的话）
                if request.name and request.name.strip().lower() != db_workflow.name.lower():
                    existing = session.exec(
                        select(BatchWorkflow).where(
                            and_(
                                BatchWorkflow.name.ilike(request.name.strip()),
                                BatchWorkflow.id != workflow_id
                            )
                        )
                    ).first()

                    if existing:
                        logger.warning(f"Workflow with name '{request.name}' already exists")
                        return None

                # 更新工作流基本信息
                if request.name is not None:
                    db_workflow.name = request.name.strip()
                if request.description is not None:
                    db_workflow.description = request.description.strip()

                # 如果提供了步骤信息，更新步骤
                if request.steps is not None:
                    # 验证所有指令ID是否存在
                    command_ids = [step.command_id for step in request.steps]
                    existing_commands = session.exec(
                        select(Command).where(Command.id.in_(command_ids))
                    ).all()
                    
                    existing_command_ids = {cmd.id for cmd in existing_commands}
                    missing_command_ids = set(command_ids) - existing_command_ids
                    
                    if missing_command_ids:
                        logger.warning(f"Commands not found: {missing_command_ids}")
                        return None

                    # 删除现有步骤
                    existing_steps = session.exec(
                        select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
                    ).all()
                    
                    for step in existing_steps:
                        session.delete(step)

                    # 创建新步骤
                    for step_data in request.steps:
                        new_step = WorkflowStep(
                            id=str(uuid.uuid4()),
                            workflow_id=workflow_id,
                            command_id=step_data.command_id,
                            step_order=step_data.step_order,
                            delay_ms=step_data.delay_ms,
                            retry_count=step_data.retry_count,
                            timeout_ms=step_data.timeout_ms
                        )
                        session.add(new_step)

                session.add(db_workflow)
                session.commit()
                session.refresh(db_workflow)

                logger.info(f"Updated workflow: {db_workflow.name}")
                
                # 返回完整的工作流信息
                return await self.get_workflow_by_id(workflow_id)

        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {e}")
            return None

    async def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        try:
            with self._get_session() as session:
                # 查找要删除的工作流
                db_workflow = session.exec(
                    select(BatchWorkflow).where(BatchWorkflow.id == workflow_id)
                ).first()

                if not db_workflow:
                    logger.warning(f"Workflow with id {workflow_id} not found")
                    return False

                # 删除相关的步骤
                existing_steps = session.exec(
                    select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
                ).all()
                
                for step in existing_steps:
                    session.delete(step)

                # 删除相关的执行记录（可选，或者保留用于审计）
                # 这里我们保留执行记录，但可以根据需要删除

                # 删除工作流
                session.delete(db_workflow)
                session.commit()

                logger.info(f"Deleted workflow with id: {workflow_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return False

    async def execute_workflow(self, workflow_id: str) -> Optional[ExecuteWorkflowResponse]:
        """执行工作流"""
        try:
            # 检查工作流是否存在
            workflow = await self.get_workflow_by_id(workflow_id)
            if not workflow:
                logger.warning(f"Workflow {workflow_id} not found")
                return None

            if not workflow.steps:
                logger.warning(f"Workflow {workflow_id} has no steps")
                return None

            # 检查是否已经在执行中
            if workflow_id in self._running_executions:
                logger.warning(f"Workflow {workflow_id} is already running")
                return None

            # 创建执行记录
            execution_id = str(uuid.uuid4())
            
            with self._get_session() as session:
                new_execution = WorkflowExecution(
                    id=execution_id,
                    workflow_id=workflow_id,
                    status="pending",
                    total_steps=len(workflow.steps),
                    completed_steps=0
                )
                session.add(new_execution)
                session.commit()

            logger.info(f"Created execution {execution_id} for workflow {workflow_id}")

            # 异步执行工作流
            asyncio.create_task(self._execute_workflow_async(execution_id, workflow))

            return ExecuteWorkflowResponse(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_name=workflow.name,
                status="pending",
                total_steps=len(workflow.steps)
            )

        except Exception as e:
            logger.error(f"Error starting workflow execution {workflow_id}: {e}")
            return None

    async def _execute_workflow_async(self, execution_id: str, workflow: WorkflowSchema):
        """异步执行工作流"""
        try:
            self._running_executions[workflow.id] = True
            
            with self._get_session() as session:
                # 更新执行状态为运行中
                execution = session.exec(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                ).first()
                
                if not execution:
                    logger.error(f"Execution {execution_id} not found")
                    return

                execution.status = "running"
                execution.started_at = datetime.now()
                session.add(execution)
                session.commit()

            logger.info(f"Starting workflow execution {execution_id}")

            # 执行每个步骤
            completed_steps = 0
            for step in workflow.steps:
                if workflow.id not in self._running_executions:
                    # 执行被取消
                    logger.info(f"Workflow execution {execution_id} was cancelled")
                    await self._update_execution_status(execution_id, "cancelled", completed_steps)
                    return

                # 执行单个步骤
                step_success = await self._execute_step(execution_id, step)
                
                if step_success:
                    completed_steps += 1
                    await self._update_execution_progress(execution_id, completed_steps)
                else:
                    # 步骤失败，终止执行
                    logger.error(f"Step {step.step_order} failed, stopping execution {execution_id}")
                    await self._update_execution_status(execution_id, "failed", completed_steps, 
                                                      f"Step {step.step_order} failed")
                    return

                # 步骤间延迟
                if step.delay_ms > 0:
                    await asyncio.sleep(step.delay_ms / 1000.0)

            # 所有步骤执行完成
            await self._update_execution_status(execution_id, "completed", completed_steps)
            logger.info(f"Workflow execution {execution_id} completed successfully")

        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {e}")
            await self._update_execution_status(execution_id, "failed", completed_steps, str(e))
        finally:
            # 清理运行状态
            if workflow.id in self._running_executions:
                del self._running_executions[workflow.id]

    async def _execute_step(self, execution_id: str, step: WorkflowStepSchema) -> bool:
        """执行单个步骤"""
        step_execution_id = str(uuid.uuid4())
        
        try:
            # 创建步骤执行记录
            with self._get_session() as session:
                step_execution = StepExecution(
                    id=step_execution_id,
                    workflow_execution_id=execution_id,
                    step_id=step.id,
                    status="running",
                    started_at=datetime.now(),
                    command_sent=step.command_content,
                    retry_attempt=0
                )
                session.add(step_execution)
                session.commit()

            logger.info(f"Executing step {step.step_order}: {step.command_content}")

            # 实际发送指令
            max_retries = step.retry_count + 1  # 包括初始尝试
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # 更新重试次数
                    with self._get_session() as session:
                        step_execution = session.exec(
                            select(StepExecution).where(StepExecution.id == step_execution_id)
                        ).first()
                        if step_execution:
                            step_execution.retry_attempt = attempt
                            session.add(step_execution)
                            session.commit()

                    # 发送指令，使用步骤的超时设置
                    result = await asyncio.wait_for(
                        serial_service.send_at_command(step.command_content),
                        timeout=step.timeout_ms / 1000.0
                    )
                    
                    # 检查响应是否符合预期
                    if result.received_data:
                        response = result.received_data.strip()
                        
                        # 简单的成功判断逻辑（可以根据需要扩展）
                        is_success = (
                            "OK" in response.upper() or 
                            "SUCCESS" in response.upper() or
                            (step.command_content.startswith("AT") and not "ERROR" in response.upper())
                        )
                        
                        # 如果有预期响应，检查是否匹配（从关联的指令获取）
                        expected_response = getattr(step, 'command_expected_response', None)
                        if expected_response and expected_response.strip():
                            is_success = expected_response.lower() in response.lower()
                        
                        if is_success:
                            # 更新步骤执行状态为成功
                            with self._get_session() as session:
                                step_execution = session.exec(
                                    select(StepExecution).where(StepExecution.id == step_execution_id)
                                ).first()
                                
                                if step_execution:
                                    step_execution.status = "completed"
                                    step_execution.finished_at = datetime.now()
                                    step_execution.response_received = response
                                    session.add(step_execution)
                                    session.commit()

                            logger.info(f"Step {step.step_order} executed successfully")
                            return True
                        else:
                            last_error = f"Unexpected response: {response}"
                            logger.warning(f"Step {step.step_order} attempt {attempt + 1} failed: {last_error}")
                    else:
                        last_error = "No response received"
                        logger.warning(f"Step {step.step_order} attempt {attempt + 1} failed: {last_error}")
                        
                except asyncio.TimeoutError:
                    last_error = f"Command timeout after {step.timeout_ms}ms"
                    logger.warning(f"Step {step.step_order} attempt {attempt + 1} timed out")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Step {step.step_order} attempt {attempt + 1} failed: {last_error}")
                
                # 如果不是最后一次尝试，等待一小段时间再重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
            
            # 所有尝试都失败了
            with self._get_session() as session:
                step_execution = session.exec(
                    select(StepExecution).where(StepExecution.id == step_execution_id)
                ).first()
                
                if step_execution:
                    step_execution.status = "failed"
                    step_execution.finished_at = datetime.now()
                    step_execution.error_message = last_error or "All retry attempts failed"
                    session.add(step_execution)
                    session.commit()

            logger.error(f"Step {step.step_order} failed after {max_retries} attempts: {last_error}")
            return False

        except Exception as e:
            logger.error(f"Error executing step {step.step_order}: {e}")
            
            # 更新步骤执行状态为失败
            try:
                with self._get_session() as session:
                    step_execution = session.exec(
                        select(StepExecution).where(StepExecution.id == step_execution_id)
                    ).first()
                    
                    if step_execution:
                        step_execution.status = "failed"
                        step_execution.finished_at = datetime.now()
                        step_execution.error_message = str(e)
                        session.add(step_execution)
                        session.commit()
            except Exception as db_error:
                logger.error(f"Error updating step execution status: {db_error}")

            return False

    async def _update_execution_progress(self, execution_id: str, completed_steps: int):
        """更新执行进度"""
        try:
            with self._get_session() as session:
                execution = session.exec(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                ).first()
                
                if execution:
                    execution.completed_steps = completed_steps
                    session.add(execution)
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating execution progress: {e}")

    async def _update_execution_status(self, execution_id: str, status: str, completed_steps: int, error_message: str = None):
        """更新执行状态"""
        try:
            with self._get_session() as session:
                execution = session.exec(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                ).first()
                
                if execution:
                    execution.status = status
                    execution.completed_steps = completed_steps
                    execution.finished_at = datetime.now()
                    if error_message:
                        execution.error_message = error_message
                    session.add(execution)
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating execution status: {e}")

    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecutionStatus]:
        """获取执行状态"""
        try:
            with self._get_session() as session:
                # 联查执行记录和工作流信息
                query = (
                    select(WorkflowExecution, BatchWorkflow)
                    .join(BatchWorkflow, WorkflowExecution.workflow_id == BatchWorkflow.id)
                    .where(WorkflowExecution.id == execution_id)
                )
                
                result = session.exec(query).first()
                if not result:
                    return None

                execution, workflow = result

                # 获取步骤执行状态
                step_executions = await self._get_step_executions(session, execution_id)

                return WorkflowExecutionStatus(
                    id=execution.id,
                    workflow_id=execution.workflow_id,
                    workflow_name=workflow.name,
                    status=execution.status,
                    started_at=execution.started_at,
                    finished_at=execution.finished_at,
                    total_steps=execution.total_steps,
                    completed_steps=execution.completed_steps,
                    error_message=execution.error_message,
                    created_at=execution.created_at,
                    steps=step_executions
                )
        except Exception as e:
            logger.error(f"Error getting execution status {execution_id}: {e}")
            return None

    async def _get_step_executions(self, session: Session, execution_id: str) -> List[StepExecutionStatus]:
        """获取步骤执行状态"""
        try:
            # 联查步骤执行、工作流步骤和指令信息
            query = (
                select(StepExecution, WorkflowStep, Command)
                .join(WorkflowStep, StepExecution.step_id == WorkflowStep.id)
                .join(Command, WorkflowStep.command_id == Command.id)
                .where(StepExecution.workflow_execution_id == execution_id)
                .order_by(WorkflowStep.step_order)
            )
            
            results = session.exec(query).all()
            
            step_executions = []
            for step_exec, step, command in results:
                step_status = StepExecutionStatus(
                    id=step_exec.id,
                    step_id=step_exec.step_id,
                    status=step_exec.status,
                    started_at=step_exec.started_at,
                    finished_at=step_exec.finished_at,
                    command_sent=step_exec.command_sent,
                    response_received=step_exec.response_received,
                    retry_attempt=step_exec.retry_attempt,
                    error_message=step_exec.error_message,
                    created_at=step_exec.created_at,
                    step_order=step.step_order,
                    command_name=command.name,
                    command_content=command.command
                )
                step_executions.append(step_status)
            
            return step_executions
        except Exception as e:
            logger.error(f"Error getting step executions: {e}")
            return []

    async def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        try:
            with self._get_session() as session:
                execution = session.exec(
                    select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
                ).first()
                
                if not execution:
                    logger.warning(f"Execution {execution_id} not found")
                    return False

                if execution.status not in ["pending", "running"]:
                    logger.warning(f"Execution {execution_id} cannot be cancelled (status: {execution.status})")
                    return False

                # 从运行状态中移除
                if execution.workflow_id in self._running_executions:
                    del self._running_executions[execution.workflow_id]

                # 更新状态
                execution.status = "cancelled"
                execution.finished_at = datetime.now()
                session.add(execution)
                session.commit()

                logger.info(f"Cancelled execution {execution_id}")
                return True

        except Exception as e:
            logger.error(f"Error cancelling execution {execution_id}: {e}")
            return False


# 创建全局实例
workflow_service = WorkflowService()