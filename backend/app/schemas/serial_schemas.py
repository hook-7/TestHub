"""
Serial Communication API Schemas for AT Commands
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


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
    baudrate: int = Field(default=115200, description="波特率")  # 优化后的默认值
    bytesize: int = Field(default=8, description="数据位")
    parity: str = Field(default="N", description="校验位 (N/E/O)")
    stopbits: int = Field(default=1, description="停止位")
    timeout: float = Field(default=0.5, description="超时时间(秒)")  # 优化后的默认值


class SerialConnectionStatus(BaseModel):
    """串口连接状态"""
    connected: bool = Field(..., description="是否连接")
    port: Optional[str] = Field(None, description="当前端口")
    baudrate: Optional[int] = Field(None, description="波特率")
    bytesize: Optional[int] = Field(None, description="数据位")
    parity: Optional[str] = Field(None, description="校验位")
    stopbits: Optional[int] = Field(None, description="停止位")
    timeout: Optional[float] = Field(None, description="超时时间")


class RawDataRequest(BaseModel):
    """原始数据请求"""
    data: str = Field(..., min_length=1, max_length=1000, description="数据字符串(AT指令或十六进制)")
    
    @field_validator('data')
    @classmethod
    def validate_data(cls, v: str) -> str:
        """验证数据格式"""
        if not v.strip():
            raise ValueError('数据不能为空')
        
        # 检查是否为16进制数据（只包含0-9, A-F, a-f和空格）
        clean_data = v.replace(' ', '').replace('\t', '').replace('\n', '')
        if clean_data and all(c in '0123456789ABCDEFabcdef' for c in clean_data):
            # 16进制数据验证
            if len(clean_data) % 2 != 0:
                raise ValueError('十六进制数据长度必须为偶数')
        
        return v.strip()


class RawDataResponse(BaseModel):
    """原始数据响应"""
    sent_data: str = Field(..., description="发送的数据")
    received_data: str = Field(..., description="接收的数据")
    timestamp: float = Field(..., description="时间戳")