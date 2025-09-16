"""
Custom Middleware for FastAPI
自定义中间件
"""

import time
import uuid
import logging
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {client_ip} - Started"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- {response.status_code} - {process_time:.3f}s"
        )
        
        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response


class GlobalRedirectMiddleware(BaseHTTPMiddleware):
    """全局路由拦截中间件 - 将未匹配的路由重定向到根目录"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        # 排除的路径，这些路径不会被重定向
        self.exclude_paths = exclude_paths or [
            "/api/",  # API路径
            "/docs",  # API文档
            "/redoc",  # ReDoc文档
            "/openapi.json",  # OpenAPI规范
            "/favicon.ico",  # 网站图标
            "/static/",  # 静态文件
            "/assets/",  # 前端资源
            "/ws",  # WebSocket连接
        ]
    
    async def dispatch(self, request: Request, call_next):
        # 检查请求路径是否应该被排除
        path = request.url.path
        
        # 检查是否匹配排除路径
        should_exclude = any(path.startswith(exclude) for exclude in self.exclude_paths)
        
        if not should_exclude:
            # 对于非API和非静态资源的请求，重定向到根目录
            logger.info(f"Redirecting unmatched route: {path} -> /")
            return RedirectResponse(url="/", status_code=302)
        
        # 继续处理请求
        response = await call_next(request)
        return response