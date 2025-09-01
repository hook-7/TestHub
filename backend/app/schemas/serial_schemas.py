"""
Serial Communication API Schemas
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class SerialPortInfo(BaseModel):
    """串口信息"""
    device: str = Field(..., description="设备路径")
    name: str = Field(..., description="设备名称")
    description: str = Field(..., description="设备描述")
    hwid: str = Field(..., description="硬件ID")
    manufacturer: str = Field(..., description="制造商")


class SerialConfig(BaseModel):
    """串口配置"""
    port: str = Field(..., description="串口设备路径")
    baudrate: int = Field(default=9600, description="波特率")
    bytesize: int = Field(default=8, description="数据位")
    parity: str = Field(default="N", description="校验位 (N/E/O)")
    stopbits: int = Field(default=1, description="停止位")
    timeout: float = Field(default=1.0, description="超时时间(秒)")


class SerialConnectionStatus(BaseModel):
    """串口连接状态"""
    connected: bool = Field(..., description="是否连接")
    port: Optional[str] = Field(None, description="当前端口")
    baudrate: Optional[int] = Field(None, description="波特率")
    bytesize: Optional[int] = Field(None, description="数据位")
    parity: Optional[str] = Field(None, description="校验位")
    stopbits: Optional[int] = Field(None, description="停止位")
    timeout: Optional[float] = Field(None, description="超时时间")


class ReadRegistersRequest(BaseModel):
    """读取寄存器请求"""
    slave_id: int = Field(..., ge=1, le=247, description="从站ID")
    start_addr: int = Field(..., ge=0, le=65535, description="起始地址")
    count: int = Field(..., ge=1, le=125, description="寄存器数量")
    function_code: int = Field(default=3, description="功能码 (3=保持寄存器, 4=输入寄存器)")


class WriteRegisterRequest(BaseModel):
    """写入单个寄存器请求"""
    slave_id: int = Field(..., ge=1, le=247, description="从站ID")
    addr: int = Field(..., ge=0, le=65535, description="寄存器地址")
    value: int = Field(..., ge=0, le=65535, description="寄存器值")


class WriteRegistersRequest(BaseModel):
    """写入多个寄存器请求"""
    slave_id: int = Field(..., ge=1, le=247, description="从站ID")
    start_addr: int = Field(..., ge=0, le=65535, description="起始地址")
    values: List[int] = Field(..., min_items=1, max_items=123, description="寄存器值列表")


class RegisterData(BaseModel):
    """寄存器数据"""
    address: int = Field(..., description="寄存器地址")
    value: int = Field(..., description="寄存器值")


class ReadRegistersResponse(BaseModel):
    """读取寄存器响应"""
    slave_id: int = Field(..., description="从站ID")
    start_addr: int = Field(..., description="起始地址")
    count: int = Field(..., description="寄存器数量")
    registers: List[RegisterData] = Field(..., description="寄存器数据")


class WriteResponse(BaseModel):
    """写入响应"""
    slave_id: int = Field(..., description="从站ID")
    success: bool = Field(..., description="写入是否成功")
    message: str = Field(..., description="响应消息")


class RawDataRequest(BaseModel):
    """原始数据请求"""
    data: str = Field(..., description="十六进制数据字符串")


class RawDataResponse(BaseModel):
    """原始数据响应"""
    sent_data: str = Field(..., description="发送的数据(十六进制)")
    received_data: str = Field(..., description="接收的数据(十六进制)")
    timestamp: float = Field(..., description="时间戳")