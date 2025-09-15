"""
Custom Exceptions and Error Handling for AT Command Communication
AT指令通信异常定义和错误处理
"""

from enum import Enum
from typing import Any, Optional


class ErrorCode(Enum):
    """标准化错误码"""
    # 成功
    SUCCESS = 0
    
    # 系统错误 (400-599)
    PARAM_ERROR = 400
    SYSTEM_ERROR = 500
    
    # 配置错误 (1200-1299)
    CONFIG_INVALID_PARAMS = 1203
    
    # 会话相关错误 (1300-1399)
    SESSION_ALREADY_EXISTS = 1301
    SESSION_NOT_FOUND = 1302
    SESSION_EXPIRED = 1303
    SESSION_ACCESS_DENIED = 1304


class HMIException(Exception):
    """HMI系统基础异常类"""
    
    def __init__(self, error_code: ErrorCode, message: str, details: Any = None):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(self.message)




class ConfigException(HMIException):
    """配置相关异常"""
    pass


class SessionException(HMIException):
    """会话相关异常"""
    pass


# 错误消息映射
ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "操作成功",
    
    # 系统错误
    ErrorCode.PARAM_ERROR: "参数错误",
    ErrorCode.SYSTEM_ERROR: "系统内部错误",
    
    # 配置错误
    ErrorCode.CONFIG_INVALID_PARAMS: "无效的配置参数",
    
    # 会话错误
    ErrorCode.SESSION_ALREADY_EXISTS: "已有客户端连接，请稍后再试",
    ErrorCode.SESSION_NOT_FOUND: "会话不存在",
    ErrorCode.SESSION_EXPIRED: "会话已过期",
    ErrorCode.SESSION_ACCESS_DENIED: "会话访问被拒绝",
}


def get_error_message(error_code: ErrorCode, custom_message: Optional[str] = None) -> str:
    """获取错误消息"""
    if custom_message:
        return custom_message
    return ERROR_MESSAGES.get(error_code, "未知错误")