"""
Serial Communication Service
"""

import logging
import time
from typing import List, Optional, Dict, Any
from app.drivers.serial_driver import serial_driver
from app.drivers.rs485_protocol import RS485Manager, RS485Command
from app.core.exceptions import SerialException, ErrorCode
from app.schemas.serial_schemas import (
    SerialPortInfo, SerialConfig, SerialConnectionStatus,
    ReadRegistersRequest, WriteRegisterRequest, WriteRegistersRequest,
    ReadRegistersResponse, WriteResponse, RegisterData, RawDataResponse
)

logger = logging.getLogger(__name__)


class SerialService:
    """串口通信服务"""
    
    def __init__(self):
        self.rs485_manager = RS485Manager(serial_driver)
    
    async def get_available_ports(self) -> List[SerialPortInfo]:
        """获取可用串口列表"""
        try:
            ports_data = serial_driver.get_available_ports()
            return [SerialPortInfo(**port) for port in ports_data]
        except Exception as e:
            logger.error(f"Error getting available ports: {e}")
            raise SerialException(ErrorCode.SYSTEM_ERROR, "获取串口列表失败")
    
    async def auto_detect_port(self) -> str:
        """自动检测串口"""
        try:
            port = serial_driver.auto_detect_port()
            if port is None:
                raise SerialException(ErrorCode.SERIAL_NO_PORTS, "未检测到可用串口")
            return port
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error auto-detecting port: {e}")
            raise SerialException(ErrorCode.SYSTEM_ERROR, "自动检测串口失败")
    
    async def connect_serial(self, config: SerialConfig) -> bool:
        """连接串口"""
        try:
            success = await serial_driver.connect(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=config.timeout
            )
            
            if not success:
                raise SerialException(ErrorCode.SERIAL_CONNECT_FAILED, f"无法连接到串口 {config.port}")
            
            logger.info(f"Connected to serial port: {config.port}")
            return True
            
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error connecting to serial port: {e}")
            raise SerialException(ErrorCode.SERIAL_CONNECT_FAILED, f"串口连接异常: {str(e)}")
    
    async def disconnect_serial(self) -> bool:
        """断开串口连接"""
        try:
            await serial_driver.disconnect()
            logger.info("Serial port disconnected")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting serial port: {e}")
            raise SerialException(ErrorCode.SERIAL_DISCONNECT_FAILED, f"断开串口连接失败: {str(e)}")
    
    async def get_connection_status(self) -> SerialConnectionStatus:
        """获取连接状态"""
        try:
            info = serial_driver.get_connection_info()
            return SerialConnectionStatus(**info)
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            raise SerialException(ErrorCode.SYSTEM_ERROR, "获取连接状态失败")
    
    async def read_registers(self, request: ReadRegistersRequest) -> ReadRegistersResponse:
        """读取寄存器"""
        try:
            if not serial_driver.is_connected:
                raise SerialException(ErrorCode.SERIAL_NOT_CONNECTED, "串口未连接")
            
            # 确定功能码
            function_code = (RS485Command.READ_HOLDING_REGISTERS 
                           if request.function_code == 3 
                           else RS485Command.READ_INPUT_REGISTERS)
            
            # 读取数据
            values = await self.rs485_manager.read_registers(
                request.slave_id, 
                request.start_addr, 
                request.count,
                function_code
            )
            
            if values is None:
                raise SerialException(ErrorCode.SERIAL_READ_FAILED, "读取寄存器无响应")
            
            # 构建响应
            registers = []
            for i, value in enumerate(values):
                registers.append(RegisterData(
                    address=request.start_addr + i,
                    value=value
                ))
            
            return ReadRegistersResponse(
                slave_id=request.slave_id,
                start_addr=request.start_addr,
                count=request.count,
                registers=registers
            )
            
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error reading registers: {e}")
            raise SerialException(ErrorCode.SERIAL_READ_FAILED, f"读取寄存器异常: {str(e)}")
    
    async def write_register(self, request: WriteRegisterRequest) -> WriteResponse:
        """写入单个寄存器"""
        try:
            if not serial_driver.is_connected:
                raise SerialException(ErrorCode.SERIAL_NOT_CONNECTED, "串口未连接")
            
            success = await self.rs485_manager.write_register(
                request.slave_id,
                request.addr,
                request.value
            )
            
            if not success:
                raise SerialException(ErrorCode.SERIAL_WRITE_FAILED, "寄存器写入失败")
            
            return WriteResponse(
                slave_id=request.slave_id,
                success=True,
                message="写入成功"
            )
            
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error writing register: {e}")
            raise SerialException(ErrorCode.SERIAL_WRITE_FAILED, f"写入寄存器异常: {str(e)}")
    
    async def write_registers(self, request: WriteRegistersRequest) -> WriteResponse:
        """写入多个寄存器"""
        try:
            if not serial_driver.is_connected:
                raise SerialException(ErrorCode.SERIAL_NOT_CONNECTED, "串口未连接")
            
            success = await self.rs485_manager.write_registers(
                request.slave_id,
                request.start_addr,
                request.values
            )
            
            if not success:
                raise SerialException(ErrorCode.SERIAL_WRITE_FAILED, "批量写入寄存器失败")
            
            return WriteResponse(
                slave_id=request.slave_id,
                success=True,
                message=f"成功写入{len(request.values)}个寄存器"
            )
            
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error writing registers: {e}")
            raise SerialException(ErrorCode.SERIAL_WRITE_FAILED, f"批量写入寄存器异常: {str(e)}")
    
    async def send_raw_data(self, hex_data: str) -> RawDataResponse:
        """发送原始数据"""
        try:
            if not serial_driver.is_connected:
                raise SerialException(ErrorCode.SERIAL_NOT_CONNECTED, "串口未连接")
            
            # 转换十六进制字符串为字节
            try:
                data = bytes.fromhex(hex_data.replace(" ", ""))
            except ValueError as e:
                raise SerialException(ErrorCode.SERIAL_INVALID_DATA, "无效的十六进制数据格式")
            
            timestamp = time.time()
            
            # 发送数据并读取响应
            response = await serial_driver.write_read(data)
            
            return RawDataResponse(
                sent_data=data.hex().upper(),
                received_data=response.hex().upper(),
                timestamp=timestamp
            )
            
        except SerialException:
            raise
        except Exception as e:
            logger.error(f"Error sending raw data: {e}")
            raise SerialException(ErrorCode.SERIAL_WRITE_FAILED, f"发送原始数据失败: {str(e)}")


# Global service instance
serial_service = SerialService()