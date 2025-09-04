"""
工作流执行引擎
"""
import asyncio
import uuid
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor

from app.schemas.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
    StepType,
    UserConfirmationRequest,
    WorkflowStepResult,
    WebSocketMessage
)

logger = logging.getLogger(__name__)


class VariableResolver:
    """变量解析器"""
    
    def __init__(self, variables: Dict[str, Any]):
        self.variables = variables
    
    def resolve(self, text: str) -> str:
        """解析文本中的变量引用"""
        if not text:
            return text
        
        # 支持 ${variable_name} 格式的变量引用
        def replace_var(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, f"${{{var_name}}}"))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, serial_service=None, websocket_manager=None):
        self.executions: Dict[str, WorkflowExecution] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.serial_service = serial_service
        self.websocket_manager = websocket_manager
        self.user_confirmations: Dict[str, Dict] = {}
        
        # 初始化示例工作流
        self._init_example_workflows()
    
    def _init_example_workflows(self):
        """初始化示例工作流"""
        # AT指令测试工作流
        at_test_workflow = WorkflowDefinition(
            workflow_id="at_command_test",
            name="AT指令测试流程",
            description="标准的AT指令测试序列，包含设备信息查询和功能测试",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    name="发送AT测试指令",
                    step_type=StepType.SERIAL_SEND,
                    description="发送AT指令测试连接",
                    serial_command="AT",
                    expected_response="OK",
                    next_step_id="step_2"
                ),
                WorkflowStep(
                    step_id="step_2", 
                    name="获取设备信息",
                    step_type=StepType.SERIAL_SEND,
                    description="查询设备版本信息",
                    serial_command="AT+GMR",
                    expected_response=r".*OK.*",
                    variable_name="device_info",
                    variable_source="response",
                    next_step_id="step_3"
                ),
                WorkflowStep(
                    step_id="step_3",
                    name="用户确认设备信息",
                    step_type=StepType.USER_CONFIRM,
                    description="请确认设备信息是否正确",
                    confirm_message="设备信息: ${device_info}\n\n是否继续测试？",
                    confirm_options=["继续", "重新获取", "停止"],
                    next_step_id="step_4"
                ),
                WorkflowStep(
                    step_id="step_4",
                    name="设置测试参数",
                    step_type=StepType.SET_VARIABLE,
                    description="设置测试相关参数",
                    variable_name="test_start_time",
                    variable_value="${current_time}",
                    next_step_id="step_5"
                ),
                WorkflowStep(
                    step_id="step_5",
                    name="执行功能测试",
                    step_type=StepType.SERIAL_SEND,
                    description="执行设备功能测试",
                    serial_command="AT+CFUN?",
                    expected_response=r"\+CFUN:\s*\d+.*OK",
                    next_step_id="step_6"
                ),
                WorkflowStep(
                    step_id="step_6",
                    name="记录测试结果",
                    step_type=StepType.LOG,
                    description="记录测试完成信息",
                    variable_name="test_result",
                    variable_value="AT指令测试完成 - 设备: ${device_info}, 时间: ${test_start_time}"
                )
            ],
            start_step_id="step_1",
            variables={
                "device_info": "",
                "test_start_time": "",
                "test_result": ""
            }
        )
        
        # 设备重启工作流
        device_restart_workflow = WorkflowDefinition(
            workflow_id="device_restart",
            name="设备重启流程",
            description="安全的设备重启流程，包含状态检查和确认",
            steps=[
                WorkflowStep(
                    step_id="restart_1",
                    name="检查设备状态",
                    step_type=StepType.SERIAL_SEND,
                    description="检查当前设备状态",
                    serial_command="AT+CFUN?",
                    expected_response=r"\+CFUN:\s*\d+.*OK",
                    variable_name="current_status",
                    variable_source="response",
                    next_step_id="restart_2"
                ),
                WorkflowStep(
                    step_id="restart_2",
                    name="用户确认重启",
                    step_type=StepType.USER_CONFIRM,
                    description="确认是否重启设备",
                    confirm_message="当前设备状态: ${current_status}\n\n⚠️ 重启设备将中断当前连接，确定要继续吗？",
                    confirm_options=["确认重启", "取消"],
                    next_step_id="restart_3"
                ),
                WorkflowStep(
                    step_id="restart_3",
                    name="执行重启命令",
                    step_type=StepType.SERIAL_SEND,
                    description="发送设备重启指令",
                    serial_command="AT+CFUN=1,1",
                    expected_response="OK",
                    response_timeout=10,
                    next_step_id="restart_4"
                ),
                WorkflowStep(
                    step_id="restart_4",
                    name="等待设备重启",
                    step_type=StepType.DELAY,
                    description="等待设备重启完成",
                    delay_seconds=15,
                    next_step_id="restart_5"
                ),
                WorkflowStep(
                    step_id="restart_5",
                    name="验证重启结果",
                    step_type=StepType.SERIAL_SEND,
                    description="验证设备是否重启成功",
                    serial_command="AT",
                    expected_response="OK",
                    retry_count=3,
                    next_step_id="restart_6"
                ),
                WorkflowStep(
                    step_id="restart_6",
                    name="记录重启结果",
                    step_type=StepType.LOG,
                    description="记录设备重启完成",
                    variable_name="restart_result",
                    variable_value="设备重启成功 - 时间: ${current_time}"
                )
            ],
            start_step_id="restart_1",
            variables={
                "current_status": "",
                "restart_result": "",
                "current_time": ""
            }
        )
        
        self.workflows[at_test_workflow.workflow_id] = at_test_workflow
        self.workflows[device_restart_workflow.workflow_id] = device_restart_workflow
    
    async def start_workflow(self, workflow_id: str, input_variables: Dict[str, Any] = None,
                           operator_id: str = None, workstation_id: str = None) -> WorkflowExecution:
        """启动工作流执行"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        
        # 初始化执行实例
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            current_step_id=workflow.start_step_id,
            variables={**workflow.variables, **(input_variables or {})},
            started_by=operator_id,
            workstation_id=workstation_id,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        logger.info(f"工作流开始执行 - 执行ID: {execution_id}, 工作流: {workflow.name}")
        
        # 异步执行工作流
        asyncio.create_task(self._execute_workflow(execution_id))
        
        return execution
    
    async def _execute_workflow(self, execution_id: str):
        """执行工作流主循环"""
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        resolver = VariableResolver(execution.variables)
        
        try:
            while execution.status == WorkflowStatus.RUNNING:
                current_step = self._get_step_by_id(workflow, execution.current_step_id)
                if not current_step:
                    break
                
                logger.info(f"执行步骤: {current_step.name} ({current_step.step_id})")
                
                # 执行步骤
                step_result = await self._execute_step(execution, current_step, resolver)
                
                # 保存步骤结果
                execution.step_results[current_step.step_id] = step_result.model_dump()
                
                # 根据结果决定下一步
                if step_result.status == StepStatus.SUCCESS:
                    next_step_id = self._get_next_step_id(current_step, step_result, resolver)
                    if next_step_id:
                        execution.current_step_id = next_step_id
                    else:
                        execution.status = WorkflowStatus.COMPLETED
                        execution.completed_at = datetime.now()
                        break
                elif step_result.status == StepStatus.FAILED:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = step_result.error_message
                    execution.failed_step_id = current_step.step_id
                    break
                elif step_result.status == StepStatus.WAITING:
                    execution.status = WorkflowStatus.PAUSED
                    break
                
                # 发送状态更新到WebSocket客户端
                await self._send_websocket_update(execution, current_step, step_result)
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"工作流执行失败: {execution_id} - {e}")
    
    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep, 
                          resolver: VariableResolver) -> WorkflowStepResult:
        """执行单个步骤"""
        start_time = datetime.now()
        
        try:
            if step.step_type == StepType.SERIAL_SEND:
                return await self._execute_serial_step(step, resolver)
            elif step.step_type == StepType.USER_CONFIRM:
                return await self._execute_confirm_step(execution, step, resolver)
            elif step.step_type == StepType.SET_VARIABLE:
                return await self._execute_variable_step(step, resolver)
            elif step.step_type == StepType.DELAY:
                return await self._execute_delay_step(step)
            elif step.step_type == StepType.LOG:
                return await self._execute_log_step(step, resolver)
            else:
                raise ValueError(f"不支持的步骤类型: {step.step_type}")
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _execute_serial_step(self, step: WorkflowStep, resolver: VariableResolver) -> WorkflowStepResult:
        """执行串口步骤"""
        start_time = datetime.now()
        
        # 解析串口指令中的变量
        command = resolver.resolve(step.serial_command)
        
        logger.info(f"发送串口指令: {command}")
        
        try:
            # 发送串口指令
            if self.serial_service:
                response = await self.serial_service.send_command(command, timeout=step.response_timeout)
            else:
                # 模拟串口响应
                await asyncio.sleep(1)
                response = "OK" if "AT" in command else f"Response to {command}"
            
            # 验证响应
            if step.expected_response:
                if not re.search(step.expected_response, response):
                    raise ValueError(f"串口响应不匹配，期望: {step.expected_response}, 实际: {response}")
            
            # 保存响应到变量
            if step.variable_name and step.variable_source == "response":
                resolver.set_variable(step.variable_name, response)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.SUCCESS,
                input_data=command,
                output_data=response,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                input_data=command,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _execute_confirm_step(self, execution: WorkflowExecution, step: WorkflowStep, 
                                  resolver: VariableResolver) -> WorkflowStepResult:
        """执行用户确认步骤"""
        # 解析确认消息中的变量
        confirm_message = resolver.resolve(step.confirm_message)
        
        # 生成确认请求ID
        confirm_key = f"{execution.execution_id}_{step.step_id}"
        
        # 发送WebSocket确认请求
        if self.websocket_manager:
            ws_message = WebSocketMessage(
                message_type="user_confirmation_request",
                execution_id=execution.execution_id,
                step_id=step.step_id,
                data={
                    "message": confirm_message,
                    "options": step.confirm_options or ["确认", "取消"],
                    "step_name": step.name,
                    "step_description": step.description
                }
            )
            await self.websocket_manager.broadcast_to_workstation(
                execution.workstation_id, 
                ws_message.model_dump()
            )
        
        logger.info(f"等待用户确认: {step.name}")
        
        # 等待用户确认 (最多等待5分钟)
        for _ in range(300):  # 5分钟 = 300秒
            if confirm_key in self.user_confirmations:
                confirmation = self.user_confirmations.pop(confirm_key)
                
                # 保存用户输入到变量
                if step.variable_name:
                    resolver.set_variable(step.variable_name, confirmation.get("user_input", ""))
                
                if confirmation.get("confirmed"):
                    return WorkflowStepResult(
                        step_id=step.step_id,
                        status=StepStatus.SUCCESS,
                        input_data=confirm_message,
                        output_data=json.dumps(confirmation)
                    )
                else:
                    return WorkflowStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        error_message="用户取消操作"
                    )
            
            await asyncio.sleep(1)
        
        # 超时
        return WorkflowStepResult(
            step_id=step.step_id,
            status=StepStatus.FAILED,
            error_message="用户确认超时"
        )
    
    async def _execute_variable_step(self, step: WorkflowStep, resolver: VariableResolver) -> WorkflowStepResult:
        """执行变量设置步骤"""
        try:
            value = resolver.resolve(step.variable_value)
            
            # 支持特殊变量
            if value == "${current_time}":
                value = datetime.now().isoformat()
            
            resolver.set_variable(step.variable_name, value)
            
            logger.info(f"设置变量: {step.variable_name} = {value}")
            
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.SUCCESS,
                input_data=f"{step.variable_name} = {step.variable_value}",
                output_data=f"{step.variable_name} = {value}"
            )
        
        except Exception as e:
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error_message=str(e)
            )
    
    async def _execute_delay_step(self, step: WorkflowStep) -> WorkflowStepResult:
        """执行延时步骤"""
        try:
            await asyncio.sleep(step.delay_seconds)
            
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.SUCCESS,
                input_data=f"延时 {step.delay_seconds} 秒",
                execution_time=step.delay_seconds
            )
        
        except Exception as e:
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error_message=str(e)
            )
    
    async def _execute_log_step(self, step: WorkflowStep, resolver: VariableResolver) -> WorkflowStepResult:
        """执行日志步骤"""
        try:
            log_content = resolver.resolve(step.variable_value)
            
            logger.info(f"工作流日志: {log_content}")
            
            if step.variable_name:
                resolver.set_variable(step.variable_name, log_content)
            
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.SUCCESS,
                input_data=step.variable_value,
                output_data=log_content
            )
        
        except Exception as e:
            return WorkflowStepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error_message=str(e)
            )
    
    def _get_step_by_id(self, workflow: WorkflowDefinition, step_id: str) -> Optional[WorkflowStep]:
        """根据ID获取步骤"""
        for step in workflow.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def _get_next_step_id(self, step: WorkflowStep, result: WorkflowStepResult, 
                         resolver: VariableResolver) -> Optional[str]:
        """获取下一步骤ID"""
        if step.step_type == StepType.CONDITION:
            # 条件步骤的分支逻辑
            condition_result = self._evaluate_condition(step.condition_expression, resolver)
            return step.true_next_step if condition_result else step.false_next_step
        else:
            return step.next_step_id
    
    def _evaluate_condition(self, expression: str, resolver: VariableResolver) -> bool:
        """评估条件表达式"""
        # 简单的条件评估，可以扩展为更复杂的表达式解析
        resolved_expr = resolver.resolve(expression)
        try:
            return eval(resolved_expr)
        except:
            return False
    
    async def _send_websocket_update(self, execution: WorkflowExecution, 
                                   step: WorkflowStep, result: WorkflowStepResult):
        """发送WebSocket状态更新"""
        if self.websocket_manager:
            ws_message = WebSocketMessage(
                message_type="workflow_step_update",
                execution_id=execution.execution_id,
                step_id=step.step_id,
                data={
                    "step_name": step.name,
                    "step_status": result.status,
                    "execution_time": result.execution_time,
                    "output_data": result.output_data,
                    "workflow_status": execution.status
                }
            )
            await self.websocket_manager.broadcast_to_workstation(
                execution.workstation_id,
                ws_message.model_dump()
            )
    
    async def handle_user_confirmation(self, confirmation: UserConfirmationRequest):
        """处理用户确认"""
        confirm_key = f"{confirmation.execution_id}_{confirmation.step_id}"
        
        self.user_confirmations[confirm_key] = {
            "confirmed": confirmation.confirmed,
            "user_input": confirmation.user_input,
            "selected_option": confirmation.selected_option,
            "operator_notes": confirmation.operator_notes
        }
        
        logger.info(f"收到用户确认: {confirm_key}, 确认: {confirmation.confirmed}")
        
        # 如果工作流暂停，恢复执行
        execution = self.executions.get(confirmation.execution_id)
        if execution and execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            asyncio.create_task(self._execute_workflow(confirmation.execution_id))
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行实例"""
        return self.executions.get(execution_id)
    
    def get_workflows(self) -> List[WorkflowDefinition]:
        """获取所有工作流定义"""
        return list(self.workflows.values())
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self.workflows.get(workflow_id)
    
    async def pause_workflow(self, execution_id: str):
        """暂停工作流"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            logger.info(f"工作流已暂停: {execution_id}")
    
    async def resume_workflow(self, execution_id: str):
        """恢复工作流"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            asyncio.create_task(self._execute_workflow(execution_id))
            logger.info(f"工作流已恢复: {execution_id}")
    
    async def cancel_workflow(self, execution_id: str):
        """取消工作流"""
        execution = self.executions.get(execution_id)
        if execution and execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            logger.info(f"工作流已取消: {execution_id}")


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()