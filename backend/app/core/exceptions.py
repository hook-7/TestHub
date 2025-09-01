"""
Custom Exceptions and Error Handling
统一异常定义和错误处理
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
    
    # 串口相关业务错误 (1000-1099)
    SERIAL_NO_PORTS = 1001
    SERIAL_CONNECT_FAILED = 1002
    SERIAL_DISCONNECT_FAILED = 1003
    SERIAL_NOT_CONNECTED = 1004
    SERIAL_READ_FAILED = 1005
    SERIAL_WRITE_FAILED = 1006
    SERIAL_INVALID_DATA = 1007
    SERIAL_TIMEOUT = 1008
    SERIAL_DEVICE_ERROR = 1009
    
    # 通信协议错误 (1100-1199)
    PROTOCOL_CRC_ERROR = 1101
    PROTOCOL_INVALID_RESPONSE = 1102
    PROTOCOL_SLAVE_ERROR = 1103
    PROTOCOL_FUNCTION_ERROR = 1104
    
    # 配置错误 (1200-1299)
    CONFIG_INVALID_PORT = 1201
    CONFIG_INVALID_BAUDRATE = 1202
    CONFIG_INVALID_PARAMS = 1203


class HMIException(Exception):
    """HMI系统基础异常类"""
    
    def __init__(self, error_code: ErrorCode, message: str, details: Any = None):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(self.message)


class SerialException(HMIException):
    """串口相关异常"""
    pass


class ProtocolException(HMIException):
    """协议相关异常"""
    pass


class ConfigException(HMIException):
    """配置相关异常"""
    pass


# 错误消息映射
ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "操作成功",
    
    # 系统错误
    ErrorCode.PARAM_ERROR: "参数错误",
    ErrorCode.SYSTEM_ERROR: "系统内部错误",
    
    # 串口错误
    ErrorCode.SERIAL_NO_PORTS: "未检测到可用串口",
    ErrorCode.SERIAL_CONNECT_FAILED: "串口连接失败",
    ErrorCode.SERIAL_DISCONNECT_FAILED: "串口断开失败", 
    ErrorCode.SERIAL_NOT_CONNECTED: "串口未连接",
    ErrorCode.SERIAL_READ_FAILED: "串口读取失败",
    ErrorCode.SERIAL_WRITE_FAILED: "串口写入失败",
    ErrorCode.SERIAL_INVALID_DATA: "无效的串口数据格式",
    ErrorCode.SERIAL_TIMEOUT: "串口通信超时",
    ErrorCode.SERIAL_DEVICE_ERROR: "串口设备错误",
    
    # 协议错误
    ErrorCode.PROTOCOL_CRC_ERROR: "协议校验错误",
    ErrorCode.PROTOCOL_INVALID_RESPONSE: "协议响应无效",
    ErrorCode.PROTOCOL_SLAVE_ERROR: "从站设备错误",
    ErrorCode.PROTOCOL_FUNCTION_ERROR: "协议功能码错误",
    
    # 配置错误
    ErrorCode.CONFIG_INVALID_PORT: "无效的串口配置",
    ErrorCode.CONFIG_INVALID_BAUDRATE: "无效的波特率配置",
    ErrorCode.CONFIG_INVALID_PARAMS: "无效的配置参数",
}


def get_error_message(error_code: ErrorCode, custom_message: Optional[str] = None) -> str:
    """获取错误消息"""
    if custom_message:
        return custom_message
    return ERROR_MESSAGES.get(error_code, "未知错误")