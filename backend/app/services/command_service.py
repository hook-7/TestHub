"""
Command Service
常用指令管理服务 - 使用SQLModel数据库
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select, and_, or_

from app.core.database import engine, Command
from app.core.config import settings
from app.schemas.command_schemas import SavedCommand, CreateCommandRequest, UpdateCommandRequest

logger = logging.getLogger(__name__)


class CommandService:
    """常用指令管理服务 - 使用数据库"""

    def __init__(self):
        logger.info("Command service initialized with database storage")

    def _get_session(self):
        """获取数据库会话"""
        return Session(engine)

    def _command_to_schema(self, db_command: Command) -> SavedCommand:
        """将数据库模型转换为API schema"""
        return SavedCommand(
            id=db_command.id,
            name=db_command.name,
            command=db_command.command,
            description=db_command.description,
            expected_response=db_command.expected_response,
            send_as_hex=db_command.send_as_hex,
            show_notification=db_command.show_notification,
            target_serial_id=db_command.target_serial_id,
            created_at=db_command.created_at
        )
    
    async def get_all_commands(self) -> List[SavedCommand]:
        """获取所有常用指令"""
        try:
            with self._get_session() as session:
                # 查询所有指令，按创建时间降序排序
                db_commands = session.exec(
                    select(Command).order_by(Command.created_at.desc())
                ).all()

                commands = [self._command_to_schema(cmd) for cmd in db_commands]
                logger.debug(f"Loaded {len(commands)} commands from database")
                return commands
        except Exception as e:
            logger.error(f"Error getting all commands: {e}")
            return []
    
    async def get_command_by_id(self, command_id: str) -> Optional[SavedCommand]:
        """根据ID获取指令"""
        try:
            with self._get_session() as session:
                db_command = session.exec(
                    select(Command).where(Command.id == command_id)
                ).first()

                if db_command:
                    return self._command_to_schema(db_command)
                return None
        except Exception as e:
            logger.error(f"Error getting command by id {command_id}: {e}")
            return None
    
    async def create_command(self, request: CreateCommandRequest) -> Optional[SavedCommand]:
        """创建新的常用指令"""
        try:
            with self._get_session() as session:
                # 检查是否已存在相同名称的指令
                existing = session.exec(
                    select(Command).where(
                        and_(
                            Command.name.ilike(request.name.strip()),
                            Command.command == request.command.strip()
                        )
                    )
                ).first()

                if existing:
                    logger.warning(f"Similar command already exists: {request.name}")
                    return None

                # 创建新指令
                new_command = Command(
                    id=str(uuid.uuid4()),
                    name=request.name.strip(),
                    command=request.command.strip(),
                    description=request.description.strip(),
                    expected_response=request.expected_response.strip(),
                    send_as_hex=request.send_as_hex,
                    show_notification=request.show_notification,
                    target_serial_id=request.target_serial_id
                )

                session.add(new_command)
                session.commit()
                session.refresh(new_command)

                logger.info(f"Created new command: {new_command.name}")
                return self._command_to_schema(new_command)

        except Exception as e:
            logger.error(f"Error creating command: {e}")
            return None
    
    async def update_command(self, command_id: str, request: UpdateCommandRequest) -> Optional[SavedCommand]:
        """更新指令"""
        try:
            with self._get_session() as session:
                # 查找要更新的指令
                db_command = session.exec(
                    select(Command).where(Command.id == command_id)
                ).first()

                if not db_command:
                    logger.warning(f"Command with id {command_id} not found")
                    return None

                # 检查名称冲突（如果要更新名称的话）
                if request.name and request.name.strip().lower() != db_command.name.lower():
                    existing = session.exec(
                        select(Command).where(
                            and_(
                                Command.name.ilike(request.name.strip()),
                                Command.id != command_id
                            )
                        )
                    ).first()

                    if existing:
                        logger.warning(f"Command with name '{request.name}' already exists")
                        return None

                # 更新字段
                if request.name is not None:
                    db_command.name = request.name.strip()
                if request.command is not None:
                    db_command.command = request.command.strip()
                if request.description is not None:
                    db_command.description = request.description.strip()
                if request.expected_response is not None:
                    db_command.expected_response = request.expected_response.strip()
                if request.send_as_hex is not None:
                    db_command.send_as_hex = request.send_as_hex
                if request.show_notification is not None:
                    db_command.show_notification = request.show_notification
                if request.target_serial_id is not None:
                    db_command.target_serial_id = request.target_serial_id

                session.add(db_command)
                session.commit()
                session.refresh(db_command)

                logger.info(f"Updated command: {db_command.name}")
                return self._command_to_schema(db_command)

        except Exception as e:
            logger.error(f"Error updating command {command_id}: {e}")
            return None
    
    async def delete_command(self, command_id: str) -> bool:
        """删除指令"""
        try:
            with self._get_session() as session:
                # 查找要删除的指令
                db_command = session.exec(
                    select(Command).where(Command.id == command_id)
                ).first()

                if not db_command:
                    logger.warning(f"Command with id {command_id} not found")
                    return False

                session.delete(db_command)
                session.commit()

                logger.info(f"Deleted command with id: {command_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting command {command_id}: {e}")
            return False
    
    async def get_commands_count(self) -> int:
        """获取指令总数"""
        try:
            with self._get_session() as session:
                count = session.exec(
                    select(Command)
                ).all()
                return len(count)
        except Exception as e:
            logger.error(f"Error getting commands count: {e}")
            return 0


# 创建全局实例
command_service = CommandService()