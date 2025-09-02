"""
Command Service
常用指令管理服务
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.schemas.command_schemas import SavedCommand, CreateCommandRequest, UpdateCommandRequest

logger = logging.getLogger(__name__)


class CommandService:
    """常用指令管理服务"""
    
    def __init__(self):
        self.commands_file = settings.COMMANDS_FILE
        logger.info(f"Commands storage file: {self.commands_file}")
    
    def _ensure_file_exists(self) -> None:
        """确保存储文件存在"""
        if not self.commands_file.exists():
            self.commands_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_commands([])
            logger.info(f"Created commands storage file: {self.commands_file}")
    
    def _load_commands(self) -> List[SavedCommand]:
        """从文件加载指令"""
        try:
            self._ensure_file_exists()
            
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            commands = []
            for item in data:
                # 处理时间戳转换
                if isinstance(item.get('created_at'), (int, float)):
                    item['created_at'] = datetime.fromtimestamp(item['created_at'] / 1000)
                elif isinstance(item.get('created_at'), str):
                    try:
                        item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                    except ValueError:
                        item['created_at'] = datetime.now()
                else:
                    item['created_at'] = datetime.now()
                
                commands.append(SavedCommand(**item))
            
            return commands
            
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading commands: {e}")
            return []
    
    def _save_commands(self, commands: List[SavedCommand]) -> bool:
        """保存指令到文件"""
        try:
            # 转换为可序列化的字典列表
            data = []
            for cmd in commands:
                cmd_dict = {
                    "id": cmd.id,
                    "name": cmd.name,
                    "command": cmd.command,
                    "description": cmd.description,
                    "created_at": int(cmd.created_at.timestamp() * 1000)  # 毫秒时间戳
                }
                data.append(cmd_dict)
            
            # 写入文件，确保原子性
            temp_file = self.commands_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            temp_file.replace(self.commands_file)
            
            logger.debug(f"Saved {len(commands)} commands to {self.commands_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving commands: {e}")
            return False
    
    async def get_all_commands(self) -> List[SavedCommand]:
        """获取所有常用指令"""
        try:
            commands = self._load_commands()
            # 按创建时间降序排序（最新的在前面）
            commands.sort(key=lambda x: x.created_at, reverse=True)
            logger.debug(f"Loaded {len(commands)} commands")
            return commands
        except Exception as e:
            logger.error(f"Error getting all commands: {e}")
            return []
    
    async def get_command_by_id(self, command_id: str) -> Optional[SavedCommand]:
        """根据ID获取指令"""
        try:
            commands = self._load_commands()
            for cmd in commands:
                if cmd.id == command_id:
                    return cmd
            return None
        except Exception as e:
            logger.error(f"Error getting command by id {command_id}: {e}")
            return None
    
    async def create_command(self, request: CreateCommandRequest) -> Optional[SavedCommand]:
        """创建新的常用指令"""
        try:
            commands = self._load_commands()
            
            # 检查是否已存在相同名称的指令
            if any(cmd.name.strip().lower() == request.name.strip().lower() for cmd in commands):
                logger.warning(f"Command with name '{request.name}' already exists")
                return None
            
            # 创建新指令
            new_command = SavedCommand(
                id=str(uuid.uuid4()),
                name=request.name.strip(),
                command=request.command.strip(),
                description=request.description.strip(),
                created_at=datetime.now()
            )
            
            # 添加到列表开头
            commands.insert(0, new_command)
            
            # 保存到文件
            if self._save_commands(commands):
                logger.info(f"Created new command: {new_command.name}")
                return new_command
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error creating command: {e}")
            return None
    
    async def update_command(self, command_id: str, request: UpdateCommandRequest) -> Optional[SavedCommand]:
        """更新指令"""
        try:
            commands = self._load_commands()
            
            # 查找要更新的指令
            target_command = None
            for i, cmd in enumerate(commands):
                if cmd.id == command_id:
                    target_command = cmd
                    break
            
            if not target_command:
                logger.warning(f"Command with id {command_id} not found")
                return None
            
            # 检查名称冲突（如果要更新名称的话）
            if request.name and request.name.strip().lower() != target_command.name.lower():
                if any(cmd.name.strip().lower() == request.name.strip().lower() for cmd in commands if cmd.id != command_id):
                    logger.warning(f"Command with name '{request.name}' already exists")
                    return None
            
            # 更新字段
            if request.name is not None:
                target_command.name = request.name.strip()
            if request.command is not None:
                target_command.command = request.command.strip()
            if request.description is not None:
                target_command.description = request.description.strip()
            
            # 保存到文件
            if self._save_commands(commands):
                logger.info(f"Updated command: {target_command.name}")
                return target_command
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error updating command {command_id}: {e}")
            return None
    
    async def delete_command(self, command_id: str) -> bool:
        """删除指令"""
        try:
            commands = self._load_commands()
            
            # 查找并删除指令
            original_count = len(commands)
            commands = [cmd for cmd in commands if cmd.id != command_id]
            
            if len(commands) == original_count:
                logger.warning(f"Command with id {command_id} not found")
                return False
            
            # 保存到文件
            if self._save_commands(commands):
                logger.info(f"Deleted command with id: {command_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting command {command_id}: {e}")
            return False
    
    async def get_commands_count(self) -> int:
        """获取指令总数"""
        try:
            commands = self._load_commands()
            return len(commands)
        except Exception as e:
            logger.error(f"Error getting commands count: {e}")
            return 0


# 创建全局实例
command_service = CommandService()