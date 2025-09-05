"""
Database Configuration and Models
使用SQLModel进行数据库连接和模型定义
"""

from sqlmodel import SQLModel, Field, Column, create_engine, Session
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from typing import Optional
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 在开发模式下显示SQL语句
    connect_args={"check_same_thread": False},  # SQLite需要这个参数
)


def create_db_and_tables():
    """创建数据库表"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


# SQLModel模型定义
class Command(SQLModel, table=True):
    """常用指令模型"""
    __tablename__ = "commands"

    id: Optional[str] = Field(default=None, primary_key=True, description="指令ID")
    name: str = Field(description="指令名称", max_length=100)
    command: str = Field(description="指令内容", max_length=1000)
    description: str = Field(description="指令描述", max_length=500)
    expected_response: str = Field(default="", description="期望返回值", max_length=1000)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True


class BatchWorkflow(SQLModel, table=True):
    """批量作业工作流模型"""
    __tablename__ = "batch_workflows"

    id: Optional[str] = Field(default=None, primary_key=True, description="工作流ID")
    name: str = Field(description="工作流名称", max_length=100)
    description: str = Field(default="", description="工作流描述", max_length=500)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True


class WorkflowStep(SQLModel, table=True):
    """工作流步骤模型"""
    __tablename__ = "workflow_steps"

    id: Optional[str] = Field(default=None, primary_key=True, description="步骤ID")
    workflow_id: str = Field(description="所属工作流ID", foreign_key="batch_workflows.id")
    command_id: str = Field(description="关联的指令ID", foreign_key="commands.id")
    step_order: int = Field(description="执行顺序", ge=1)
    delay_ms: int = Field(default=1000, description="执行后延迟时间(毫秒)", ge=0)
    retry_count: int = Field(default=0, description="重试次数", ge=0)
    timeout_ms: int = Field(default=5000, description="超时时间(毫秒)", ge=100)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True


class WorkflowExecution(SQLModel, table=True):
    """工作流执行记录模型"""
    __tablename__ = "workflow_executions"

    id: Optional[str] = Field(default=None, primary_key=True, description="执行记录ID")
    workflow_id: str = Field(description="工作流ID", foreign_key="batch_workflows.id")
    status: str = Field(description="执行状态", default="pending")  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    finished_at: Optional[datetime] = Field(default=None, description="结束时间")
    total_steps: int = Field(description="总步骤数", ge=0)
    completed_steps: int = Field(default=0, description="已完成步骤数", ge=0)
    error_message: Optional[str] = Field(default=None, description="错误信息", max_length=1000)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True


class StepExecution(SQLModel, table=True):
    """步骤执行记录模型"""
    __tablename__ = "step_executions"

    id: Optional[str] = Field(default=None, primary_key=True, description="步骤执行ID")
    workflow_execution_id: str = Field(description="工作流执行ID", foreign_key="workflow_executions.id")
    step_id: str = Field(description="步骤ID", foreign_key="workflow_steps.id")
    status: str = Field(description="执行状态", default="pending")  # pending, running, completed, failed, skipped
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    finished_at: Optional[datetime] = Field(default=None, description="结束时间")
    command_sent: Optional[str] = Field(default=None, description="发送的指令", max_length=1000)
    response_received: Optional[str] = Field(default=None, description="接收的响应", max_length=2000)
    retry_attempt: int = Field(default=0, description="重试次数", ge=0)
    error_message: Optional[str] = Field(default=None, description="错误信息", max_length=1000)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True
