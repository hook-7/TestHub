"""
RS485 Communication Protocol Handler
"""

import struct
import logging
from typing import Optional, List, Union, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class RS485Command(Enum):
    """RS485命令类型"""
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_REGISTERS = 0x10


class RS485Protocol:
    """RS485协议处理器 (基于Modbus RTU)"""
    
    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """计算CRC16校验码"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    @staticmethod
    def create_read_command(slave_id: int, start_addr: int, count: int, 
                          function_code: RS485Command = RS485Command.READ_HOLDING_REGISTERS) -> bytes:
        """创建读取命令"""
        try:
            # 构建命令数据
            data = struct.pack(">BBHHx", slave_id, function_code.value, start_addr, count)[:-1]
            
            # 计算CRC
            crc = RS485Protocol.calculate_crc16(data)
            
            # 添加CRC (小端序)
            command = data + struct.pack("<H", crc)
            
            logger.debug(f"Created read command: {command.hex()}")
            return command
            
        except Exception as e:
            logger.error(f"Error creating read command: {e}")
            raise
    
    @staticmethod
    def create_write_command(slave_id: int, start_addr: int, 
                           values: Union[int, List[int]]) -> bytes:
        """创建写入命令"""
        try:
            if isinstance(values, int):
                # 写单个寄存器
                data = struct.pack(">BBHH", slave_id, RS485Command.WRITE_SINGLE_REGISTER.value, 
                                 start_addr, values)
            else:
                # 写多个寄存器
                count = len(values)
                byte_count = count * 2
                data = struct.pack(">BBHHB", slave_id, RS485Command.WRITE_MULTIPLE_REGISTERS.value,
                                 start_addr, count, byte_count)
                
                # 添加寄存器值
                for value in values:
                    data += struct.pack(">H", value)
            
            # 计算CRC
            crc = RS485Protocol.calculate_crc16(data)
            
            # 添加CRC (小端序)
            command = data + struct.pack("<H", crc)
            
            logger.debug(f"Created write command: {command.hex()}")
            return command
            
        except Exception as e:
            logger.error(f"Error creating write command: {e}")
            raise
    
    @staticmethod
    def parse_response(response: bytes, expected_slave_id: int) -> Optional[Dict]:
        """解析响应数据"""
        try:
            if len(response) < 5:  # 最小响应长度
                logger.warning(f"Response too short: {len(response)} bytes")
                return None
            
            # 验证CRC
            data_without_crc = response[:-2]
            received_crc = struct.unpack("<H", response[-2:])[0]
            calculated_crc = RS485Protocol.calculate_crc16(data_without_crc)
            
            if received_crc != calculated_crc:
                logger.error(f"CRC mismatch: received={received_crc:04X}, calculated={calculated_crc:04X}")
                return None
            
            # 解析基本信息
            slave_id = response[0]
            function_code = response[1]
            
            if slave_id != expected_slave_id:
                logger.warning(f"Slave ID mismatch: expected={expected_slave_id}, received={slave_id}")
                return None
            
            # 检查是否为错误响应
            if function_code & 0x80:
                error_code = response[2]
                logger.error(f"Device error response: function={function_code:02X}, error={error_code:02X}")
                return {
                    "slave_id": slave_id,
                    "function_code": function_code,
                    "error": True,
                    "error_code": error_code
                }
            
            # 解析正常响应
            result = {
                "slave_id": slave_id,
                "function_code": function_code,
                "error": False,
                "data": []
            }
            
            if function_code in [RS485Command.READ_HOLDING_REGISTERS.value, 
                               RS485Command.READ_INPUT_REGISTERS.value]:
                # 读取响应
                byte_count = response[2]
                register_data = response[3:3+byte_count]
                
                # 解析寄存器值 (大端序)
                values = []
                for i in range(0, len(register_data), 2):
                    value = struct.unpack(">H", register_data[i:i+2])[0]
                    values.append(value)
                
                result["data"] = values
                result["byte_count"] = byte_count
                
            elif function_code in [RS485Command.WRITE_SINGLE_REGISTER.value,
                                 RS485Command.WRITE_MULTIPLE_REGISTERS.value]:
                # 写入响应确认
                if function_code == RS485Command.WRITE_SINGLE_REGISTER.value:
                    addr, value = struct.unpack(">HH", response[2:6])
                    result["address"] = addr
                    result["value"] = value
                else:
                    addr, count = struct.unpack(">HH", response[2:6])
                    result["address"] = addr
                    result["count"] = count
            
            logger.debug(f"Parsed response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None


class RS485Manager:
    """RS485通信管理器"""
    
    def __init__(self, driver: 'SerialDriver'):
        self.driver = driver
        self.protocol = RS485Protocol()
    
    async def read_registers(self, slave_id: int, start_addr: int, count: int,
                           function_code: RS485Command = RS485Command.READ_HOLDING_REGISTERS) -> Optional[List[int]]:
        """读取寄存器"""
        try:
            if not self.driver.is_connected:
                raise RuntimeError("Serial port not connected")
            
            # 创建读取命令
            command = self.protocol.create_read_command(slave_id, start_addr, count, function_code)
            
            # 发送命令并读取响应
            response = await self.driver.write_read(command)
            
            if not response:
                logger.warning("No response received")
                return None
            
            # 解析响应
            parsed = self.protocol.parse_response(response, slave_id)
            
            if parsed and not parsed.get("error", True):
                return parsed.get("data", [])
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading registers: {e}")
            return None
    
    async def write_register(self, slave_id: int, addr: int, value: int) -> bool:
        """写入单个寄存器"""
        try:
            if not self.driver.is_connected:
                raise RuntimeError("Serial port not connected")
            
            # 创建写入命令
            command = self.protocol.create_write_command(slave_id, addr, value)
            
            # 发送命令并读取响应
            response = await self.driver.write_read(command)
            
            if not response:
                logger.warning("No response received")
                return False
            
            # 解析响应
            parsed = self.protocol.parse_response(response, slave_id)
            
            if parsed and not parsed.get("error", True):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error writing register: {e}")
            return False
    
    async def write_registers(self, slave_id: int, start_addr: int, values: List[int]) -> bool:
        """写入多个寄存器"""
        try:
            if not self.driver.is_connected:
                raise RuntimeError("Serial port not connected")
            
            # 创建写入命令
            command = self.protocol.create_write_command(slave_id, start_addr, values)
            
            # 发送命令并读取响应
            response = await self.driver.write_read(command)
            
            if not response:
                logger.warning("No response received")
                return False
            
            # 解析响应
            parsed = self.protocol.parse_response(response, slave_id)
            
            if parsed and not parsed.get("error", True):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error writing registers: {e}")
            return False