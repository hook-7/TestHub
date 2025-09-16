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
    ALLOWED_ORIGINS: List[str] = ["*"]  
    
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database settings - 数据库配置
    DB_NAME: str = Field(default="testhub.db", description="SQLite数据库文件名")
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
        db_path = self.DATA_DIR / self.DB_NAME
        return f"sqlite:///{db_path}"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "env_prefix": "HMI_",
        "validate_assignment": True,
        "extra": "ignore"  # 忽略额外的环境变量
    }


settings = Settings()