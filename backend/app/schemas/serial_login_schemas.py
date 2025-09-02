"""
Serial Login Configuration Schemas
串口登录配置相关的数据模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SerialLoginConfig(BaseModel):
    """串口登录配置"""
    port: str = Field(..., description="串口设备路径")
    baudrate: int = Field(default=9600, description="波特率")
    bytesize: int = Field(default=8, description="数据位")
    parity: str = Field(default="N", description="校验位 (N/E/O)")
    stopbits: int = Field(default=1, description="停止位")
    timeout: float = Field(default=1.0, description="超时时间(秒)")
    auto_connect: bool = Field(default=False, description="是否自动连接")
    login_command: Optional[str] = Field(None, description="登录命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    retry_count: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")


class SerialLoginConfigResponse(BaseModel):
    """串口登录配置响应"""
    id: int = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    port: str = Field(..., description="串口设备路径")
    baudrate: int = Field(..., description="波特率")
    bytesize: int = Field(..., description="数据位")
    parity: str = Field(..., description="校验位")
    stopbits: int = Field(..., description="停止位")
    timeout: float = Field(..., description="超时时间")
    auto_connect: bool = Field(..., description="是否自动连接")
    login_command: Optional[str] = Field(None, description="登录命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    retry_count: int = Field(..., description="重试次数")
    retry_delay: float = Field(..., description="重试延迟")
    is_active: bool = Field(default=False, description="是否为当前激活配置")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class CreateSerialLoginConfigRequest(BaseModel):
    """创建串口登录配置请求"""
    name: str = Field(..., description="配置名称")
    port: str = Field(..., description="串口设备路径")
    baudrate: int = Field(default=9600, description="波特率")
    bytesize: int = Field(default=8, description="数据位")
    parity: str = Field(default="N", description="校验位 (N/E/O)")
    stopbits: int = Field(default=1, description="停止位")
    timeout: float = Field(default=1.0, description="超时时间(秒)")
    auto_connect: bool = Field(default=False, description="是否自动连接")
    login_command: Optional[str] = Field(None, description="登录命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    retry_count: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")


class UpdateSerialLoginConfigRequest(BaseModel):
    """更新串口登录配置请求"""
    name: Optional[str] = Field(None, description="配置名称")
    port: Optional[str] = Field(None, description="串口设备路径")
    baudrate: Optional[int] = Field(None, description="波特率")
    bytesize: Optional[int] = Field(None, description="数据位")
    parity: Optional[str] = Field(None, description="校验位 (N/E/O)")
    stopbits: Optional[int] = Field(None, description="停止位")
    timeout: Optional[float] = Field(None, description="超时时间(秒)")
    auto_connect: Optional[bool] = Field(None, description="是否自动连接")
    login_command: Optional[str] = Field(None, description="登录命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    retry_count: Optional[int] = Field(None, description="重试次数")
    retry_delay: Optional[float] = Field(None, description="重试延迟(秒)")


class SerialLoginTestRequest(BaseModel):
    """串口登录测试请求"""
    config_id: Optional[int] = Field(None, description="配置ID（如果为空则使用临时配置）")
    temp_config: Optional[SerialLoginConfig] = Field(None, description="临时配置")


class SerialLoginTestResponse(BaseModel):
    """串口登录测试响应"""
    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    connection_time: float = Field(..., description="连接耗时(秒)")
    login_time: Optional[float] = Field(None, description="登录耗时(秒)")
    response_data: Optional[str] = Field(None, description="设备响应数据")
    error_details: Optional[str] = Field(None, description="错误详情")