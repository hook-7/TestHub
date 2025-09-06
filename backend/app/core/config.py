"""
Application Configuration
"""

import os
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Industrial HMI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", description="服务器主机地址")
    PORT: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    DEBUG: bool = Field(default=True, description="调试模式")
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed_envs = ["development", "testing", "production"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    
    SERIAL_TIMEOUT: float = 0.5  
    SERIAL_BAUDRATE: int = 115200  
    SERIAL_BYTESIZE: int = 8
    SERIAL_PARITY: str = "N"  # None
    SERIAL_STOPBITS: int = 1
    
    # 串口自动检测配置
    AUTO_BAUDRATE_LIST: List[int] = [115200, 57600, 38400, 19200, 9600, 4800]  # 按优先级排序
    
    # Session settings - 基于心跳的会话管理
    HEARTBEAT_TIMEOUT_SECONDS: int = 60  # 心跳超时时间（秒）- 1分钟无心跳则清理会话
    HEARTBEAT_INTERVAL_SECONDS: int = 25  # 建议心跳间隔（秒）
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database settings - 数据库配置
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=5432, ge=1, le=65535, description="数据库端口")
    DB_NAME: str = Field(default="testhub", description="数据库名称")
    DB_USER: str = Field(default="postgres", description="数据库用户名")
    DB_PASSWORD: str = Field(default="postgres", description="数据库密码")
    DB_ECHO: bool = Field(default=False, description="是否显示SQL语句")
    
    # Data storage settings - 数据存储配置
    @property
    def DATA_DIR(self) -> Path:
        """获取数据存储目录（工作目录下的 data 文件夹）"""
        work_dir = Path.cwd()
        data_dir = work_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir

    @property
    def DATABASE_URL(self) -> str:
        """数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "env_prefix": "HMI_",
        "validate_assignment": True,
    }


settings = Settings()