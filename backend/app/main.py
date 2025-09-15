"""
Industrial HMI Main Application
FastAPI application with AT command communication support
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.error_handler import setup_exception_handlers
from app.core.middleware import RequestLoggingMiddleware
from app.core.config import settings

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # 创建数据库表
    from app.core.database import create_db_and_tables
    try:
        create_db_and_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    yield
    # Shutdown
    logger.info("Shutting down Industrial HMI")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## 工业上位机系统API
    
    提供完整的工业管理功能，支持：
    
    - 🔄 实时数据交互
    - 👤 会话管理
    - 📝 指令管理
    - 📊 测试结果管理
    
    ### 使用说明
    系统支持直接访问，无需登录认证。
    
    ### 数据格式
    所有响应遵循统一格式：`{"code": 0, "msg": "success", "data": {...}}`
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    contact={
        "name": "Industrial HMI Support",
        "email": "support@industrial-hmi.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "系统",
            "description": "系统健康检查和基础信息",
        },
        {
            "name": "会话管理", 
            "description": "用户会话创建、验证和管理",
        },
        {
            "name": "指令管理",
            "description": "常用指令的保存和管理",
        },
        {
            "name": "WebSocket",
            "description": "实时通信和数据推送",
        },
        {
            "name": "实时通信",
            "description": "WebSocket实时数据交互",
        },
    ],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "192.168.100.3"]
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


app.mount("/assets", StaticFiles(directory=str(settings.DATA_DIR/"dist/assets")), name="assets")
@app.get("/{path_name:path}")
async def serve_vue(path_name: str):
    return FileResponse(str(settings.DATA_DIR/"dist")+"/index.html")



