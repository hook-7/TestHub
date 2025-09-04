"""
Industrial HMI Main Application
FastAPI application with AT command communication support
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.error_handler import setup_exception_handlers
from app.core.middleware import RequestLoggingMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # 初始化工作流服务和WebSocket集成
    try:
        from app.services.workflow_service import get_workflow_service
        from app.api.v1.websocket import manager as websocket_manager
        
        workflow_service = get_workflow_service()
        workflow_service.set_websocket_manager(websocket_manager)
        logger.info("工作流服务初始化完成")
    except Exception as e:
        logger.error(f"工作流服务初始化失败: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down Industrial HMI")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## 工业上位机系统API
    
    提供完整的工业串口通信管理功能，支持：
    
    - 🔌 串口设备管理与配置
    - 📡 AT指令通信
    - 🔄 实时数据交互
    - 👤 会话管理
    - 📝 指令管理
    
    ### 认证说明
    大部分API需要有效的会话ID，请先通过 `/session/create` 创建会话。
    
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
            "name": "串口通信",
            "description": "串口设备管理和数据通信",
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
        {
            "name": "工作流管理",
            "description": "工作流定义、编辑和管理",
        },
        {
            "name": "工作流执行",
            "description": "工作流执行、监控和控制",
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

# Static files for frontend (production)
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info(f"Serving frontend from: {frontend_dist}")
else:
    logger.warning(f"Frontend dist directory not found: {frontend_dist}")



