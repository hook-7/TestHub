"""
Serial Communication Service
"""

import logging
import time
from typing import List, Optional, Dict, Any
from app.drivers.serial_driver import serial_driver
from app.drivers.rs485_protocol import RS485Manager, RS485Command
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
            return []
    
    async def auto_detect_port(self) -> Optional[str]:
        """自动检测串口"""
        try:
            return serial_driver.auto_detect_port()
        except Exception as e:
            logger.error(f"Error auto-detecting port: {e}")
            return None
    
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
            
            if success:
                logger.info(f"Connected to serial port: {config.port}")
            else:
                logger.error(f"Failed to connect to serial port: {config.port}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error connecting to serial port: {e}")
            return False
    
    async def disconnect_serial(self) -> bool:
        """断开串口连接"""
        try:
            await serial_driver.disconnect()
            logger.info("Serial port disconnected")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting serial port: {e}")
            return False
    
    async def get_connection_status(self) -> SerialConnectionStatus:
        """获取连接状态"""
        try:
            info = serial_driver.get_connection_info()
            return SerialConnectionStatus(**info)
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return SerialConnectionStatus(connected=False)
    
    async def read_registers(self, request: ReadRegistersRequest) -> Optional[ReadRegistersResponse]:
        """读取寄存器"""
        try:
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
                return None
            
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
            
        except Exception as e:
            logger.error(f"Error reading registers: {e}")
            return None
    
    async def write_register(self, request: WriteRegisterRequest) -> WriteResponse:
        """写入单个寄存器"""
        try:
            success = await self.rs485_manager.write_register(
                request.slave_id,
                request.addr,
                request.value
            )
            
            message = "写入成功" if success else "写入失败"
            
            return WriteResponse(
                slave_id=request.slave_id,
                success=success,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error writing register: {e}")
            return WriteResponse(
                slave_id=request.slave_id,
                success=False,
                message=f"写入错误: {str(e)}"
            )
    
    async def write_registers(self, request: WriteRegistersRequest) -> WriteResponse:
        """写入多个寄存器"""
        try:
            success = await self.rs485_manager.write_registers(
                request.slave_id,
                request.start_addr,
                request.values
            )
            
            message = f"写入{len(request.values)}个寄存器成功" if success else "写入失败"
            
            return WriteResponse(
                slave_id=request.slave_id,
                success=success,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error writing registers: {e}")
            return WriteResponse(
                slave_id=request.slave_id,
                success=False,
                message=f"写入错误: {str(e)}"
            )
    
    async def send_raw_data(self, hex_data: str) -> RawDataResponse:
        """发送原始数据"""
        try:
            if not serial_driver.is_connected:
                raise RuntimeError("Serial port not connected")
            
            # 转换十六进制字符串为字节
            data = bytes.fromhex(hex_data.replace(" ", ""))
            
            timestamp = time.time()
            
            # 发送数据并读取响应
            response = await serial_driver.write_read(data)
            
            return RawDataResponse(
                sent_data=data.hex().upper(),
                received_data=response.hex().upper(),
                timestamp=timestamp
            )
            
        except ValueError as e:
            logger.error(f"Invalid hex data: {e}")
            raise ValueError("无效的十六进制数据格式")
        except Exception as e:
            logger.error(f"Error sending raw data: {e}")
            raise RuntimeError(f"发送数据失败: {str(e)}")


# Global service instance
serial_service = SerialService()