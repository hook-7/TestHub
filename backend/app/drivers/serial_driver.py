"""
Serial Communication Driver for AT Commands
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
import serial
import serial.tools.list_ports
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)


class SerialDriver:
    """Serial Communication Driver for AT Commands"""
    
    def __init__(self):
        self.connection: Optional[serial.Serial] = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.is_connected = False
        self.port_config = {
            "port": None,
            "baudrate": settings.SERIAL_BAUDRATE,
            "bytesize": settings.SERIAL_BYTESIZE,
            "parity": settings.SERIAL_PARITY,
            "stopbits": settings.SERIAL_STOPBITS,
            "timeout": settings.SERIAL_TIMEOUT,
        }
    
    @staticmethod
    def get_available_ports() -> List[Dict[str, str]]:
        """获取可用串口列表"""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = []
            
            for port in ports:
                port_info = {
                    "device": port.device,
                    "name": port.name or "Unknown",
                    "description": port.description or "No description",
                    "hwid": port.hwid or "Unknown",
                    "manufacturer": getattr(port, 'manufacturer', 'Unknown') or 'Unknown',
                }
                port_list.append(port_info)
                
            logger.info(f"Found {len(port_list)} available serial ports")
            return port_list
            
        except Exception as e:
            logger.error(f"Error getting available ports: {e}")
            return []
    
    async def auto_detect_baudrate(self, port: str, test_command: bytes = b'AT\r\n') -> Optional[int]:
        """自动检测最佳波特率"""
        from app.core.config import settings
        
        for baudrate in settings.AUTO_BAUDRATE_LIST:
            try:
                logger.info(f"Testing baudrate {baudrate} on port {port}")
                
                # 临时连接测试
                test_config = self.port_config.copy()
                test_config.update({
                    "port": port,
                    "baudrate": baudrate,
                    "timeout": 0.3  # 短超时用于快速测试
                })
                
                temp_connection = None
                try:
                    # 创建临时连接
                    loop = asyncio.get_event_loop()
                    temp_connection = await loop.run_in_executor(
                        self.executor, lambda: serial.Serial(**test_config)
                    )
                    
                    # 发送测试命令
                    temp_connection.write(test_command)
                    await asyncio.sleep(0.02)  # 短暂延迟
                    
                    # 尝试读取响应
                    response = temp_connection.read(100)
                    
                    if response and len(response) > 0:
                        logger.info(f"Found working baudrate: {baudrate}")
                        return baudrate
                        
                except Exception as e:
                    logger.debug(f"Baudrate {baudrate} failed: {e}")
                finally:
                    if temp_connection and temp_connection.is_open:
                        temp_connection.close()
                        await asyncio.sleep(0.1)  # 给端口一点时间关闭
                        
            except Exception as e:
                logger.debug(f"Error testing baudrate {baudrate}: {e}")
                continue
        
        logger.warning("No working baudrate found, using default")
        return None

    @staticmethod
    def auto_detect_port() -> Optional[str]:
        """自动检测可用的串口设备"""
        try:
            ports = SerialDriver.get_available_ports()
            
            # 优先选择USB转串口设备
            for port in ports:
                description = port["description"].lower()
                hwid = port["hwid"].lower()
                
                # 常见的USB转串口芯片标识
                usb_serial_keywords = [
                    "usb", "ch340", "ch341", "cp210", "ft232", "pl2303"
                ]
                
                if any(keyword in description or keyword in hwid 
                       for keyword in usb_serial_keywords):
                    logger.info(f"Auto-detected USB serial port: {port['device']}")
                    return port["device"]
            
            # 如果没有USB转串口，返回第一个可用端口
            if ports:
                logger.info(f"Using first available port: {ports[0]['device']}")
                return ports[0]["device"]
                
            return None
            
        except Exception as e:
            logger.error(f"Error auto-detecting port: {e}")
            return None
    
    async def connect(self, port: str, auto_baudrate: bool = False, **kwargs) -> bool:
        """连接串口"""
        try:
            # 自动检测波特率
            if auto_baudrate and "baudrate" not in kwargs:
                detected_baudrate = await self.auto_detect_baudrate(port)
                if detected_baudrate:
                    kwargs["baudrate"] = detected_baudrate
                    logger.info(f"Using auto-detected baudrate: {detected_baudrate}")
            
            # 更新配置
            self.port_config.update(kwargs)
            self.port_config["port"] = port
            
            # 在线程池中执行连接
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._connect_sync)
            
            logger.info(f"Connected to serial port: {port} at {self.port_config['baudrate']} baud")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to port {port}: {e}")
            self.is_connected = False
            return False
    
    def _connect_sync(self):
        """同步连接串口"""
        if self.connection and self.connection.is_open:
            self.connection.close()
        
        self.connection = serial.Serial(**self.port_config)
        self.is_connected = True
    
    async def disconnect(self):
        """断开串口连接"""
        try:
            if self.connection and self.connection.is_open:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, self.connection.close)
            
            self.is_connected = False
            logger.info("Serial port disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting serial port: {e}")
    
    async def write_data(self, data: bytes) -> bool:
        """写入数据到串口"""
        if not self.is_connected or not self.connection:
            raise RuntimeError("Serial port not connected")
        
        try:
            loop = asyncio.get_event_loop()
            bytes_written = await loop.run_in_executor(
                self.executor, self.connection.write, data
            )
            
            logger.debug(f"Written {bytes_written} bytes: {data.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing data: {e}")
            return False
    
    async def read_data(self, size: int = 1024, timeout: Optional[float] = None) -> bytes:
        """从串口读取数据"""
        if not self.is_connected or not self.connection:
            raise RuntimeError("Serial port not connected")
        
        try:
            # 设置临时超时
            original_timeout = self.connection.timeout
            if timeout is not None:
                self.connection.timeout = timeout
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, self._read_sync, size
            )
            
            # 恢复原始超时
            self.connection.timeout = original_timeout
            
            logger.debug(f"Read {len(data)} bytes: {data.hex()}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            return b""
    
    def _read_sync(self, size: int) -> bytes:
        """同步读取数据"""
        return self.connection.read(size)
    
    def _read_until_sync(self, terminator: bytes, max_size: int = 1024) -> bytes:
        """同步读取数据直到遇到终止符"""
        data = b""
        start_time = time.time()
        timeout = self.connection.timeout or 1.0
        
        while len(data) < max_size:
            # 检查超时
            if time.time() - start_time > timeout:
                break
                
            # 读取一个字节
            char = self.connection.read(1)
            if not char:
                break
                
            data += char
            
            # 检查是否遇到终止符
            if terminator in data:
                break
                
        return data
    
    async def read_until(self, terminator: bytes = b'\r\n', max_size: int = 1024, 
                        timeout: Optional[float] = None) -> bytes:
        """读取数据直到遇到指定的终止符"""
        if not self.is_connected or not self.connection:
            raise RuntimeError("Serial port not connected")
        
        try:
            # 设置临时超时
            original_timeout = self.connection.timeout
            if timeout is not None:
                self.connection.timeout = timeout
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, self._read_until_sync, terminator, max_size
            )
            
            # 恢复原始超时
            self.connection.timeout = original_timeout
            
            logger.debug(f"Read until terminator {terminator}: {len(data)} bytes")
            return data
            
        except Exception as e:
            logger.error(f"Error reading until terminator: {e}")
            return b""
    
    async def write_read(self, data: bytes, read_size: int = 1024, 
                        read_timeout: float = 1.0, write_delay: float = 0.01) -> bytes:
        """写入数据并读取响应（固定大小）"""
        await self.write_data(data)
        
        # 给设备一点时间处理命令
        await asyncio.sleep(write_delay)
        
        return await self.read_data(read_size, read_timeout)
    
    async def write_read_until(self, data: bytes, terminator: bytes = b'\r\n', 
                              max_size: int = 1024, read_timeout: float = 1.0, 
                              write_delay: float = 0.01) -> bytes:
        """写入数据并读取响应直到遇到终止符（推荐用于AT命令）"""
        await self.write_data(data)
        
        # 给设备一点时间处理命令
        await asyncio.sleep(write_delay)
        
        return await self.read_until(terminator, max_size, read_timeout)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        if not self.connection:
            return {"connected": False}
        
        return {
            "connected": self.is_connected,
            "port": self.connection.port,
            "baudrate": self.connection.baudrate,
            "bytesize": self.connection.bytesize,
            "parity": self.connection.parity,
            "stopbits": self.connection.stopbits,
            "timeout": self.connection.timeout,
        }


# Global serial driver instance
serial_driver = SerialDriver()