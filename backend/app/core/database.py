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
