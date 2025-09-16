"""
Global Error Handler
全局异常处理中间件
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import HMIException, ErrorCode, get_error_message
from app.core.response import APIResponse

logger = logging.getLogger(__name__)


async def hmi_exception_handler(request: Request, exc: HMIException) -> JSONResponse:
    """HMI自定义异常处理器"""
    logger.warning(f"HMI Exception: {exc.error_code.name} - {exc.message}")
    
    response = APIResponse.error(
        code=exc.error_code.value,
        msg=exc.message,
        data=exc.details
    )
    
    return JSONResponse(
        status_code=200,  # 业务异常仍返回200
        content=response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    if exc.status_code == 404:
        response = APIResponse.error(404, "接口不存在")
    elif exc.status_code == 405:
        response = APIResponse.error(405, "请求方法不允许")
    elif exc.status_code == 422:
        response = APIResponse.param_error("请求参数格式错误")
    else:
        response = APIResponse.error(exc.status_code, str(exc.detail))
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """参数验证异常处理器"""
    logger.warning(f"Validation Error: {exc.errors()}")
    
    # 提取第一个错误信息
    error_msg = "参数验证失败"
    if exc.errors():
        first_error = exc.errors()[0]
        field = first_error.get('loc', ['unknown'])[-1]
        msg = first_error.get('msg', '格式错误')
        error_msg = f"参数 '{field}' {msg}"
    
    response = APIResponse.param_error(error_msg)
    
    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled Exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    response = APIResponse.system_error("系统内部错误，请联系管理员")
    
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )


def setup_exception_handlers(app):
    """设置异常处理器"""
    app.add_exception_handler(HMIException, hmi_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)