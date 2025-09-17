"""
Database Configuration and Models
使用SQLModel进行数据库连接和模型定义
"""

from sqlmodel import SQLModel, Field, Column, create_engine, Session, Relationship
from sqlalchemy import DateTime, Text, ForeignKey, Table, Integer, String, Index, UUID as SQLUUID
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import json
from uuid import uuid4, UUID
from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
def create_database_engine():
    """创建数据库引擎，根据数据库类型配置不同的连接参数"""
    connect_args = {}
    
    if settings.DB_TYPE == "sqlite":
        # SQLite特定配置
        connect_args = {"check_same_thread": False}
    elif settings.DB_TYPE == "postgresql":
        # PostgreSQL特定配置
        connect_args = {
            "options": "-c timezone=Asia/Shanghai",  # 设置时区
        }
    
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,  # 是否显示SQL语句
        connect_args=connect_args,
        pool_pre_ping=True,  # 连接池预检查，确保连接有效
        pool_recycle=3600,   # 连接回收时间（秒）
    )

# 创建数据库引擎
engine = create_database_engine()


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


# -------------------------
# 关联表定义 (必须在模型类之前定义)
# -------------------------
workflow_commands = Table(
    "workflow_commands",
    SQLModel.metadata,
    Column("workflow_id", SQLUUID(as_uuid=True), ForeignKey("workflows.id"), primary_key=True),
    Column("command_id", String(255), ForeignKey("commands.id"), primary_key=True),
    Column("order_index", Integer, nullable=False, server_default="0", comment="命令在工作流中的执行顺序"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_workflow_commands_order", "workflow_id", "order_index")
)


# SQLModel模型定义
class Command(SQLModel, table=True):
    """常用指令模型"""
    __tablename__ = "commands"

    id: Optional[str] = Field(default=None, primary_key=True, description="指令ID")
    name: str = Field(description="指令名称", max_length=100, index=True)
    command: str = Field(description="指令内容", max_length=1000)
    description: str = Field(description="指令描述", max_length=500)
    expected_response: str = Field(default="", description="期望返回值", max_length=1000)
    input_mode: str = Field(default="TEXT_INPUT", description="输入模式：TEXT_INPUT-文本输入，HEX_READ-十六进制读取，TCP_INPUT-TCP形式输入")
    show_notification: bool = Field(default=False, description="是否弹出通知")
    target_serial_id: Optional[int] = Field(default=None, description="目标串口ID，null表示使用当前选择的串口")
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    class Config:
        from_attributes = True


class TestResult(SQLModel, table=True):
    """测试结果主表"""
    __tablename__ = "test_results"

    id: Optional[str] = Field(default=None, primary_key=True, description="测试结果ID")
    mac_address: str = Field(description="MAC地址", max_length=17)
    start_time: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="开始时间"
    )
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    total_tests: int = Field(description="总测试数")
    passed_tests: int = Field(description="通过测试数")
    failed_tests: int = Field(description="失败测试数")
    skipped_tests: int = Field(description="跳过测试数")
    operator: Optional[str] = Field(default=None, description="操作员", max_length=100)
    workstation: Optional[str] = Field(default=None, description="工位", max_length=100)
    device_id: Optional[str] = Field(default=None, description="设备ID", max_length=100)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )

    # 关联关系
    test_items: List["TestItemResult"] = Relationship(back_populates="test_result")

    class Config:
        from_attributes = True


class TestItemResult(SQLModel, table=True):
    """测试项结果表"""
    __tablename__ = "test_item_results"

    id: Optional[str] = Field(default=None, primary_key=True, description="测试项结果ID")
    test_result_id: str = Field(foreign_key="test_results.id", description="测试结果ID")
    command_id: str = Field(description="指令ID", max_length=100)
    name: str = Field(description="测试项名称", max_length=200)
    command: str = Field(description="执行的命令", max_length=1000)
    expected_response: str = Field(default="", description="期望响应", max_length=1000)
    actual_response: Optional[str] = Field(default=None, description="实际响应", max_length=1000)
    is_ok: bool = Field(description="是否通过")
    reason: str = Field(description="结果原因", max_length=100)
    timestamp: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="测试时间"
    )
    has_notification: bool = Field(default=False, description="是否有通知")
    user_choice: Optional[bool] = Field(default=None, description="用户选择结果")

    # 关联关系
    test_result: Optional[TestResult] = Relationship(back_populates="test_items")

    class Config:
        from_attributes = True


# -------------------------
# 工作流表
# -------------------------
class Workflow(SQLModel, table=True):
    """工作流模型"""
    __tablename__ = "workflows"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(SQLUUID(as_uuid=True), primary_key=True),
        description="工作流ID"
    )
    name: str = Field(
        description="工作流名称", 
        max_length=200, 
        index=True,
        unique=True
    )
    description: str = Field(
        default="", 
        description="工作流描述", 
        max_length=1000
    )
    is_active: bool = Field(
        default=True, 
        description="是否启用",
        index=True
    )
    version: str = Field(
        default="1.0.0",
        description="工作流版本",
        max_length=20
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
        description="更新时间"
    )

    # 关系定义
    variables: List["WorkflowVariable"] = Relationship(
        back_populates="workflow",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    class Config:
        from_attributes = True

    # 添加复合索引
    __table_args__ = (
        Index("idx_workflows_active_name", "is_active", "name"),
    )


# -------------------------
# 工作流变量表
# -------------------------
class WorkflowVariable(SQLModel, table=True):
    """工作流变量模型"""
    __tablename__ = "workflow_variables"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(SQLUUID(as_uuid=True), primary_key=True),
        description="变量ID"
    )
    workflow_id: UUID = Field(
        sa_column=Column(SQLUUID(as_uuid=True), ForeignKey("workflows.id"), index=True),
        description="工作流ID"
    )
    name: str = Field(
        description="变量名称", 
        max_length=100, 
        index=True
    )
    description: str = Field(
        default="", 
        description="变量描述", 
        max_length=500
    )
    variable_type: str = Field(
        default="string",
        description="变量类型",
        max_length=20,
        index=True
    )
    default_value: Optional[str] = Field(
        default=None,
        description="默认值",
        max_length=1000
    )
    is_required: bool = Field(
        default=False,
        description="是否必需"
    )
    validation_rule: Optional[str] = Field(
        default=None,
        description="验证规则",
        max_length=500
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="创建时间"
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
        description="更新时间"
    )

    # 关系定义
    workflow: Optional[Workflow] = Relationship(back_populates="variables")

    class Config:
        from_attributes = True

    # 添加复合索引
    __table_args__ = (
        Index("idx_workflow_variables_workflow_type", "workflow_id", "variable_type"),
        Index("idx_workflow_variables_required", "workflow_id", "is_required"),
    )

