"""
Database Configuration and Models
使用SQLModel进行数据库连接和模型定义
"""

from sqlmodel import SQLModel, Field, Column, create_engine, Session, Relationship
from sqlalchemy import DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from typing import Optional, List
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,  # 是否显示SQL语句
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
    send_as_hex: bool = Field(default=False, description="是否以原始16进制发送")
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
