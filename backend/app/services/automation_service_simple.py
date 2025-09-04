"""
简化版自动化命令服务 (无外部依赖)
"""
import asyncio
import uuid
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from app.schemas.automation_simple import (
    AutomationCommandRequest,
    AutomationCommandResponse, 
    CommandStatus,
    CommandType,
    CommandConfirmationRequest,
    CommandTemplate
)

logger = logging.getLogger(__name__)


class AutomationServiceSimple:
    """简化版自动化命令服务"""
    
    def __init__(self):
        self.commands: Dict[str, AutomationCommandResponse] = {}
        self.templates: Dict[str, CommandTemplate] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认命令模板"""
        default_templates = [
            CommandTemplate(
                template_id="restart_device",
                name="重启设备",
                command_type=CommandType.DEVICE,
                description="重启指定设备",
                parameters_schema={
                    "device_id": {"type": "string", "required": True, "description": "设备ID"},
                    "force": {"type": "boolean", "required": False, "default": False, "description": "是否强制重启"}
                },
                requires_confirmation=True
            ),
            CommandTemplate(
                template_id="run_test_sequence",
                name="执行测试序列",
                command_type=CommandType.TEST,
                description="执行自动化测试序列",
                parameters_schema={
                    "sequence_name": {"type": "string", "required": True, "description": "测试序列名称"},
                    "product_sn": {"type": "string", "required": True, "description": "产品SN"},
                    "test_params": {"type": "object", "required": False, "description": "测试参数"}
                },
                requires_confirmation=True
            ),
            CommandTemplate(
                template_id="backup_data",
                name="备份数据",
                command_type=CommandType.MAINTENANCE,
                description="备份系统数据",
                parameters_schema={
                    "backup_path": {"type": "string", "required": False, "description": "备份路径"},
                    "include_logs": {"type": "boolean", "required": False, "default": True, "description": "是否包含日志"}
                },
                requires_confirmation=True
            ),
            CommandTemplate(
                template_id="clear_cache",
                name="清理缓存",
                command_type=CommandType.SYSTEM,
                description="清理系统缓存",
                parameters_schema={},
                requires_confirmation=False
            )
        ]
        
        for template in default_templates:
            self.templates[template.template_id] = template
    
    async def create_command(self, request: AutomationCommandRequest) -> AutomationCommandResponse:
        """创建自动化命令"""
        command_id = str(uuid.uuid4())
        now = datetime.now()
        
        command = AutomationCommandResponse(
            command_id=command_id,
            status=CommandStatus.PENDING if request.requires_confirmation else CommandStatus.CONFIRMED,
            created_at=now,
            updated_at=now
        )
        
        self.commands[command_id] = command
        
        # 记录命令创建日志
        print(f"📝 自动化命令已创建 - 命令ID: {command_id}, 类型: {request.command_type}")
        
        # 如果不需要确认，直接执行
        if not request.requires_confirmation:
            await self._execute_command_async(command_id, request)
        
        return command
    
    async def confirm_command(self, confirmation: CommandConfirmationRequest) -> AutomationCommandResponse:
        """确认命令执行"""
        command = self.commands.get(confirmation.command_id)
        if not command:
            raise ValueError(f"命令不存在: {confirmation.command_id}")
        
        if command.status != CommandStatus.PENDING:
            raise ValueError(f"命令状态无法确认: {command.status}")
        
        if confirmation.confirmed:
            command.status = CommandStatus.CONFIRMED
            command.updated_at = datetime.now()
            
            print(f"✅ 命令已确认执行 - 命令ID: {confirmation.command_id}")
            
            # 异步执行命令
            await self._execute_command_async(confirmation.command_id, None)
        else:
            command.status = CommandStatus.CANCELLED
            command.updated_at = datetime.now()
            print(f"❌ 命令已取消 - 命令ID: {confirmation.command_id}")
        
        return command
    
    async def _execute_command_async(self, command_id: str, request: Optional[AutomationCommandRequest]):
        """异步执行命令"""
        command = self.commands[command_id]
        command.status = CommandStatus.EXECUTING
        command.updated_at = datetime.now()
        
        print(f"⚡ 开始执行命令: {command_id}")
        
        try:
            # 模拟命令执行
            start_time = datetime.now()
            await asyncio.sleep(2)  # 模拟执行时间
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
            
            command.status = CommandStatus.SUCCESS
            command.execution_time = execution_time
            command.result = {
                "success": True,
                "output": f"命令执行成功",
                "timestamp": end_time.isoformat()
            }
            
            print(f"✅ 命令执行成功: {command_id}, 耗时: {execution_time:.2f}秒")
            
        except Exception as e:
            command.status = CommandStatus.FAILED
            command.error_message = str(e)
            print(f"❌ 命令执行失败: {command_id} - {e}")
        
        finally:
            command.updated_at = datetime.now()
    
    def get_command(self, command_id: str) -> Optional[AutomationCommandResponse]:
        """获取命令信息"""
        return self.commands.get(command_id)
    
    def get_commands(self, 
                    status: Optional[CommandStatus] = None,
                    command_type: Optional[CommandType] = None,
                    page: int = 1,
                    page_size: int = 10) -> Dict[str, Any]:
        """获取命令列表"""
        commands = list(self.commands.values())
        
        # 过滤
        if status:
            commands = [cmd for cmd in commands if cmd.status == status]
        if command_type:
            commands = [cmd for cmd in commands if hasattr(cmd, 'command_type')]
        
        # 排序 (按创建时间倒序)
        commands.sort(key=lambda x: x.created_at, reverse=True)
        
        # 分页
        total = len(commands)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_commands = commands[start_idx:end_idx]
        
        return {
            "commands": paginated_commands,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def get_templates(self) -> List[CommandTemplate]:
        """获取命令模板列表"""
        return [template for template in self.templates.values() if template.is_active]
    
    def get_template(self, template_id: str) -> Optional[CommandTemplate]:
        """获取指定命令模板"""
        return self.templates.get(template_id)
    
    async def execute_template_command(self, 
                                     template_id: str, 
                                     parameters: Dict[str, Any],
                                     operator_id: Optional[str] = None,
                                     workstation_id: Optional[str] = None) -> AutomationCommandResponse:
        """根据模板执行命令"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 验证参数
        self._validate_parameters(parameters, template.parameters_schema)
        
        # 创建命令请求
        request = AutomationCommandRequest(
            command_name=template.name,
            command_type=template.command_type,
            parameters=parameters,
            requires_confirmation=template.requires_confirmation,
            description=template.description,
            operator_id=operator_id,
            workstation_id=workstation_id
        )
        
        return await self.create_command(request)
    
    def _validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]):
        """验证命令参数"""
        for param_name, param_config in schema.items():
            if param_config.get("required", False) and param_name not in parameters:
                raise ValueError(f"缺少必需参数: {param_name}")
    
    async def cancel_command(self, command_id: str) -> AutomationCommandResponse:
        """取消命令执行"""
        command = self.commands.get(command_id)
        if not command:
            raise ValueError(f"命令不存在: {command_id}")
        
        if command.status in [CommandStatus.SUCCESS, CommandStatus.FAILED, CommandStatus.CANCELLED]:
            raise ValueError(f"命令无法取消，当前状态: {command.status}")
        
        command.status = CommandStatus.CANCELLED
        command.updated_at = datetime.now()
        
        print(f"🚫 命令已取消 - 命令ID: {command_id}")
        return command


# 全局实例
automation_service_simple = AutomationServiceSimple()