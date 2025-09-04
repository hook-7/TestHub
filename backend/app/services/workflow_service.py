"""
工作流服务模块
提供工作流定义、执行和管理功能
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from asteval import Interpreter

from app.schemas.workflow_schemas import (
    WorkflowDefinition, WorkflowExecution, WorkflowExecutionStatus,
    WorkflowStep, StepType, SendStep, ExpectStep, AssignStep, 
    ConfirmStep, ControlStep, ExpectType, ControlType,
    WorkflowLog
)
from app.schemas.websocket import (
    WSWorkflowLogMessage, WSWorkflowConfirmMessage, WSWorkflowStatusMessage
)
from app.services.serial_service import SerialService
from app.core.exceptions import WorkflowError, ValidationError

logger = logging.getLogger(__name__)


class VariableContext:
    """变量上下文管理器"""
    
    def __init__(self, initial_vars: Optional[Dict[str, Any]] = None):
        self.variables = initial_vars or {}
        self.interpreter = Interpreter()
        
        # 添加安全的内置函数
        self.interpreter.symtable['re'] = re
        self.interpreter.symtable['len'] = len
        self.interpreter.symtable['str'] = str
        self.interpreter.symtable['int'] = int
        self.interpreter.symtable['float'] = float
        self.interpreter.symtable['bool'] = bool
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self.variables[name] = value
        self.interpreter.symtable[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def evaluate_expression(self, expression: str) -> Any:
        """安全执行表达式"""
        try:
            # 更新解释器的符号表
            for name, value in self.variables.items():
                self.interpreter.symtable[name] = value
            
            result = self.interpreter.eval(expression)
            # 检查是否有错误（asteval 1.0+ 使用 error 而不是 errors）
            if hasattr(self.interpreter, 'error') and self.interpreter.error:
                raise ValueError(f"表达式执行错误: {self.interpreter.error}")
            elif hasattr(self.interpreter, 'errors') and self.interpreter.errors:
                raise ValueError(f"表达式执行错误: {self.interpreter.errors}")
            return result
        except Exception as e:
            logger.error(f"表达式执行失败: {expression}, 错误: {e}")
            raise WorkflowError(f"表达式执行失败: {e}")
    
    def substitute_variables(self, text: str) -> str:
        """替换文本中的变量占位符"""
        def replace_var(match):
            var_name = match.group(1)
            value = self.get_variable(var_name)
            return str(value) if value is not None else match.group(0)
        
        # 支持 ${variable} 格式的占位符
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.variables.copy()


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, serial_service: SerialService):
        self.serial_service = serial_service
        self.executions: Dict[str, WorkflowExecution] = {}
        self.execution_tasks: Dict[str, asyncio.Task] = {}
        self.confirm_callbacks: Dict[str, Callable] = {}
        self.websocket_manager = None  # 延迟初始化
    
    async def execute_workflow(
        self, 
        workflow: WorkflowDefinition, 
        initial_vars: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """执行工作流"""
        execution_id = str(uuid.uuid4())
        
        # 创建执行实例
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow.id or "unknown",
            status=WorkflowExecutionStatus.PENDING,
            variables=initial_vars or {},
            started_at=datetime.now().isoformat()
        )
        
        self.executions[execution_id] = execution
        
        # 启动异步执行任务
        task = asyncio.create_task(
            self._run_workflow(execution, workflow, session_id)
        )
        self.execution_tasks[execution_id] = task
        
        return execution_id
    
    async def _run_workflow(
        self, 
        execution: WorkflowExecution, 
        workflow: WorkflowDefinition,
        session_id: Optional[str] = None
    ) -> None:
        """运行工作流"""
        try:
            execution.status = WorkflowExecutionStatus.RUNNING
            
            # 初始化变量上下文
            context = VariableContext(workflow.variables)
            if execution.variables:
                for name, value in execution.variables.items():
                    context.set_variable(name, value)
            
            # 执行步骤
            await self._execute_steps(execution, workflow.steps, context, session_id)
            
            # 完成执行
            execution.status = WorkflowExecutionStatus.COMPLETED
            execution.completed_at = datetime.now().isoformat()
            execution.variables = context.to_dict()
            
            await self._log_execution(execution, "INFO", "工作流执行完成")
            await self._send_status_update(execution, "工作流执行完成")
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            execution.status = WorkflowExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now().isoformat()
            await self._log_execution(execution, "ERROR", f"工作流执行失败: {e}")
            await self._send_status_update(execution, f"工作流执行失败: {e}")
    
    async def _execute_steps(
        self, 
        execution: WorkflowExecution, 
        steps: List[WorkflowStep], 
        context: VariableContext,
        session_id: Optional[str] = None
    ) -> None:
        """执行步骤列表"""
        for step in steps:
            if execution.status != WorkflowExecutionStatus.RUNNING:
                break
                
            execution.current_step = step.id
            await self._execute_single_step(execution, step, context, session_id)
    
    async def _execute_single_step(
        self, 
        execution: WorkflowExecution, 
        step: WorkflowStep, 
        context: VariableContext,
        session_id: Optional[str] = None
    ) -> None:
        """执行单个步骤"""
        await self._log_execution(execution, "INFO", f"开始执行步骤: {step.name}")
        
        try:
            if step.type == StepType.SEND:
                await self._execute_send_step(execution, step, context, session_id)
            elif step.type == StepType.EXPECT:
                await self._execute_expect_step(execution, step, context, session_id)
            elif step.type == StepType.ASSIGN:
                await self._execute_assign_step(execution, step, context)
            elif step.type == StepType.CONFIRM:
                await self._execute_confirm_step(execution, step, context)
            elif step.type == StepType.CONTROL:
                await self._execute_control_step(execution, step, context, session_id)
            else:
                raise WorkflowError(f"不支持的步骤类型: {step.type}")
                
            await self._log_execution(execution, "INFO", f"步骤执行完成: {step.name}")
            
        except Exception as e:
            await self._log_execution(execution, "ERROR", f"步骤执行失败: {step.name}, 错误: {e}")
            raise
    
    async def _execute_send_step(
        self, 
        execution: WorkflowExecution, 
        step: SendStep, 
        context: VariableContext,
        session_id: Optional[str] = None
    ) -> None:
        """执行发送步骤"""
        # 替换变量占位符
        command = context.substitute_variables(step.command)
        
        # 发送指令
        if session_id:
            response = await self.serial_service.send_command(session_id, command)
            context.set_variable("last_response", response.data)
            await self._log_execution(execution, "INFO", f"发送指令: {command}, 响应: {response.data}")
        else:
            await self._log_execution(execution, "WARNING", f"无会话ID，模拟发送指令: {command}")
        
        # 延迟
        if step.delay > 0:
            await asyncio.sleep(step.delay)
    
    async def _execute_expect_step(
        self, 
        execution: WorkflowExecution, 
        step: ExpectStep, 
        context: VariableContext,
        session_id: Optional[str] = None
    ) -> None:
        """执行期望步骤"""
        last_response = context.get_variable("last_response", "")
        
        if step.expect_type == ExpectType.STRING:
            # 字符串匹配
            if step.pattern in last_response:
                await self._log_execution(execution, "INFO", f"期望匹配成功: {step.pattern}")
            else:
                raise WorkflowError(f"期望匹配失败: 期望 '{step.pattern}', 实际 '{last_response}'")
        
        elif step.expect_type == ExpectType.REGEX:
            # 正则匹配
            match = re.search(step.pattern, last_response)
            if match:
                context.set_variable("match_result", match.groups())
                await self._log_execution(execution, "INFO", f"正则匹配成功: {step.pattern}")
            else:
                raise WorkflowError(f"正则匹配失败: 模式 '{step.pattern}', 文本 '{last_response}'")
        
        elif step.expect_type == ExpectType.TIMEOUT:
            # 超时处理
            if step.on_timeout:
                result = context.evaluate_expression(step.on_timeout)
                await self._log_execution(execution, "INFO", f"超时处理执行: {result}")
    
    async def _execute_assign_step(
        self, 
        execution: WorkflowExecution, 
        step: AssignStep, 
        context: VariableContext
    ) -> None:
        """执行赋值步骤"""
        try:
            result = context.evaluate_expression(step.expression)
            context.set_variable(step.variable, result)
            await self._log_execution(execution, "INFO", f"变量赋值: {step.variable} = {result}")
        except Exception as e:
            raise WorkflowError(f"变量赋值失败: {step.variable} = {step.expression}, 错误: {e}")
    
    async def _execute_confirm_step(
        self, 
        execution: WorkflowExecution, 
        step: ConfirmStep, 
        context: VariableContext
    ) -> None:
        """执行确认步骤"""
        # 暂停执行，等待用户确认
        execution.status = WorkflowExecutionStatus.PAUSED
        
        # 创建确认回调
        confirm_future = asyncio.Future()
        self.confirm_callbacks[execution.id] = confirm_future.set_result
        
        await self._log_execution(execution, "INFO", f"等待用户确认: {step.message}")
        
        # 发送确认请求到WebSocket
        ws_confirm_msg = WSWorkflowConfirmMessage(
            execution_id=execution.id,
            step_id=step.id,
            message=step.message,
            options=step.options,
            timeout=step.timeout,
            timestamp=datetime.now().isoformat()
        )
        await self._send_websocket_message(ws_confirm_msg.model_dump())
        
        try:
            # 等待用户确认
            if step.timeout:
                result = await asyncio.wait_for(confirm_future, timeout=step.timeout)
            else:
                result = await confirm_future
            
            context.set_variable("confirm_result", result)
            execution.status = WorkflowExecutionStatus.RUNNING
            await self._log_execution(execution, "INFO", f"用户确认结果: {result}")
            
        except asyncio.TimeoutError:
            raise WorkflowError(f"用户确认超时: {step.timeout}秒")
        finally:
            # 清理回调
            if execution.id in self.confirm_callbacks:
                del self.confirm_callbacks[execution.id]
    
    async def _execute_control_step(
        self, 
        execution: WorkflowExecution, 
        step: ControlStep, 
        context: VariableContext,
        session_id: Optional[str] = None
    ) -> None:
        """执行控制步骤"""
        if step.control_type == ControlType.IF:
            if not step.condition:
                raise WorkflowError("IF控制步骤缺少条件表达式")
            
            condition_result = context.evaluate_expression(step.condition)
            if condition_result and step.steps:
                await self._execute_steps(execution, step.steps, context, session_id)
            
            await self._log_execution(execution, "INFO", f"IF条件判断: {step.condition} = {condition_result}")
        
        elif step.control_type == ControlType.LOOP:
            if not step.condition:
                raise WorkflowError("LOOP控制步骤缺少条件表达式")
            
            loop_count = 0
            max_loops = 1000  # 防止无限循环
            
            while loop_count < max_loops:
                condition_result = context.evaluate_expression(step.condition)
                if not condition_result:
                    break
                
                if step.steps:
                    await self._execute_steps(execution, step.steps, context, session_id)
                
                loop_count += 1
            
            await self._log_execution(execution, "INFO", f"LOOP执行完成，循环次数: {loop_count}")
    
    def set_websocket_manager(self, manager):
        """设置WebSocket管理器"""
        self.websocket_manager = manager
    
    async def _send_websocket_message(self, message: dict) -> None:
        """发送WebSocket消息"""
        if self.websocket_manager:
            try:
                await self.websocket_manager.broadcast(message)
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
    
    async def _log_execution(
        self, 
        execution: WorkflowExecution, 
        level: str, 
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录执行日志"""
        log_entry = WorkflowLog(
            timestamp=datetime.now().isoformat(),
            step_id=execution.current_step or "system",
            level=level,
            message=message,
            data=data
        )
        
        execution.logs.append(log_entry.model_dump())
        logger.info(f"[{execution.id}] {message}")
        
        # 发送日志到WebSocket
        ws_log_msg = WSWorkflowLogMessage(
            execution_id=execution.id,
            step_id=execution.current_step or "system",
            level=level,
            message=message,
            data=data,
            timestamp=log_entry.timestamp
        )
        await self._send_websocket_message(ws_log_msg.model_dump())
    
    async def _send_status_update(
        self, 
        execution: WorkflowExecution, 
        message: str
    ) -> None:
        """发送状态更新"""
        ws_status_msg = WSWorkflowStatusMessage(
            execution_id=execution.id,
            status=execution.status,
            current_step=execution.current_step,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        await self._send_websocket_message(ws_status_msg.model_dump())
    
    def handle_confirm_response(self, execution_id: str, action: str) -> bool:
        """处理确认响应"""
        if execution_id in self.confirm_callbacks:
            callback = self.confirm_callbacks[execution_id]
            callback(action)
            return True
        return False
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行实例"""
        return self.executions.get(execution_id)
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecutionStatus]:
        """获取执行状态"""
        execution = self.get_execution(execution_id)
        return execution.status if execution else None
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.status = WorkflowExecutionStatus.CANCELLED
            execution.completed_at = datetime.now().isoformat()
            
            # 取消异步任务
            if execution_id in self.execution_tasks:
                task = self.execution_tasks[execution_id]
                task.cancel()
                del self.execution_tasks[execution_id]
            
            return True
        return False


class WorkflowService:
    """工作流管理服务"""
    
    def __init__(self, serial_service: SerialService):
        self.serial_service = serial_service
        self.executor = WorkflowExecutor(serial_service)
        self.workflows: Dict[str, WorkflowDefinition] = {}
    
    def set_websocket_manager(self, manager):
        """设置WebSocket管理器"""
        self.executor.set_websocket_manager(manager)
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> WorkflowDefinition:
        """创建工作流"""
        try:
            workflow_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # 解析步骤
            steps = self._parse_steps(workflow_data.get("steps", []))
            
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=workflow_data["name"],
                description=workflow_data.get("description"),
                variables=workflow_data.get("variables", {}),
                steps=steps,
                created_at=now,
                updated_at=now
            )
            
            self.workflows[workflow_id] = workflow
            logger.info(f"创建工作流: {workflow.name} (ID: {workflow_id})")
            
            return workflow
            
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise ValidationError(f"工作流创建失败: {e}")
    
    def _parse_steps(self, steps_data: List[Dict[str, Any]]) -> List[WorkflowStep]:
        """解析步骤定义"""
        steps = []
        
        for step_data in steps_data:
            step_type = step_data.get("type")
            
            if step_type == StepType.SEND:
                step = SendStep(**step_data)
            elif step_type == StepType.EXPECT:
                step = ExpectStep(**step_data)
            elif step_type == StepType.ASSIGN:
                step = AssignStep(**step_data)
            elif step_type == StepType.CONFIRM:
                step = ConfirmStep(**step_data)
            elif step_type == StepType.CONTROL:
                # 递归解析子步骤
                if "steps" in step_data:
                    step_data["steps"] = self._parse_steps(step_data["steps"])
                step = ControlStep(**step_data)
            else:
                raise ValueError(f"不支持的步骤类型: {step_type}")
            
            steps.append(step)
        
        return steps
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """列出所有工作流"""
        return list(self.workflows.values())
    
    def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> Optional[WorkflowDefinition]:
        """更新工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        try:
            # 更新字段
            if "name" in update_data:
                workflow.name = update_data["name"]
            if "description" in update_data:
                workflow.description = update_data["description"]
            if "variables" in update_data:
                workflow.variables = update_data["variables"]
            if "steps" in update_data:
                workflow.steps = self._parse_steps(update_data["steps"])
            
            workflow.updated_at = datetime.now().isoformat()
            
            logger.info(f"更新工作流: {workflow.name} (ID: {workflow_id})")
            return workflow
            
        except Exception as e:
            logger.error(f"更新工作流失败: {e}")
            raise ValidationError(f"工作流更新失败: {e}")
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"删除工作流: {workflow_id}")
            return True
        return False
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        variables: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """执行工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValidationError(f"工作流不存在: {workflow_id}")
        
        return await self.executor.execute_workflow(workflow, variables, session_id)
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行实例"""
        return self.executor.get_execution(execution_id)
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecutionStatus]:
        """获取执行状态"""
        return self.executor.get_execution_status(execution_id)
    
    def handle_confirm_response(self, execution_id: str, action: str) -> bool:
        """处理确认响应"""
        return self.executor.handle_confirm_response(execution_id, action)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        return self.executor.cancel_execution(execution_id)
    
    def list_executions(self) -> List[WorkflowExecution]:
        """列出所有执行实例"""
        return list(self.executor.executions.values())


# 全局服务实例
workflow_service: Optional[WorkflowService] = None


def get_workflow_service() -> WorkflowService:
    """获取工作流服务实例"""
    global workflow_service
    if workflow_service is None:
        from app.services.serial_service import get_serial_service
        workflow_service = WorkflowService(get_serial_service())
    return workflow_service