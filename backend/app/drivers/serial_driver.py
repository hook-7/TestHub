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
    """Serial Communication Driver for AT Commands - Multi-port support"""
    
    def __init__(self):
        # 多串口连接管理
        self.connections: Dict[int, serial.Serial] = {}  # serial_id -> connection
        self.port_configs: Dict[int, Dict[str, Any]] = {}  # serial_id -> config
        self.connected_ports: Dict[int, str] = {}  # serial_id -> port_path
        self.executor = ThreadPoolExecutor(max_workers=4)  # 支持多个串口并发
        self._next_serial_id = 1  # 下一个可用的串口ID
        
        # 默认配置模板
        self.default_config = {
            "baudrate": settings.SERIAL_BAUDRATE,
            "bytesize": settings.SERIAL_BYTESIZE,
            "parity": settings.SERIAL_PARITY,
            "stopbits": settings.SERIAL_STOPBITS,
            "timeout": settings.SERIAL_TIMEOUT,
        }
    
    def get_next_serial_id(self) -> int:
        """获取下一个可用的串口ID（按连接顺序递增）"""
        serial_id = self._next_serial_id
        self._next_serial_id += 1
        return serial_id
    
    def get_connected_serials(self) -> List[Dict[str, Any]]:
        """获取所有已连接串口的信息"""
        connected = []
        for serial_id, connection in self.connections.items():
            if connection and connection.is_open:
                connected.append({
                    "serial_id": serial_id,
                    "port": self.connected_ports.get(serial_id),
                    "config": self.port_configs.get(serial_id, {}),
                    "is_connected": True
                })
        return connected
    
    def is_serial_connected(self, serial_id: int) -> bool:
        """检查指定串口是否连接"""
        connection = self.connections.get(serial_id)
        return connection is not None and connection.is_open
    
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
    
    async def connect(self, port: str, auto_baudrate: bool = False, **kwargs) -> int:
        """连接串口，返回串口ID"""
        try:
            # 检查端口是否已经被连接
            for serial_id, connected_port in self.connected_ports.items():
                if connected_port == port:
                    logger.warning(f"Port {port} already connected with serial_id {serial_id}")
                    return serial_id
            
            # 获取新的串口ID
            serial_id = self.get_next_serial_id()
            
            # 自动检测波特率
            if auto_baudrate and "baudrate" not in kwargs:
                detected_baudrate = await self.auto_detect_baudrate(port)
                if detected_baudrate:
                    kwargs["baudrate"] = detected_baudrate
                    logger.info(f"Using auto-detected baudrate: {detected_baudrate}")
            
            # 创建配置
            config = self.default_config.copy()
            config.update(kwargs)
            config["port"] = port
            
            # 在线程池中执行连接
            loop = asyncio.get_event_loop()
            connection = await loop.run_in_executor(
                self.executor, lambda: self._connect_sync(config)
            )
            
            # 保存连接信息
            self.connections[serial_id] = connection
            self.port_configs[serial_id] = config
            self.connected_ports[serial_id] = port
            
            logger.info(f"Connected to serial port: {port} at {config['baudrate']} baud with serial_id {serial_id}")
            return serial_id
            
        except Exception as e:
            logger.error(f"Failed to connect to port {port}: {e}")
            raise
    
    def _connect_sync(self, config: Dict[str, Any]) -> serial.Serial:
        """同步连接串口"""
        return serial.Serial(**config)
    
    async def disconnect(self, serial_id: int = None):
        """断开串口连接"""
        try:
            if serial_id is None:
                # 断开所有连接
                for sid in list(self.connections.keys()):
                    await self.disconnect(sid)
                return
            
            connection = self.connections.get(serial_id)
            if connection and connection.is_open:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, connection.close)
            
            # 清理连接信息
            if serial_id in self.connections:
                del self.connections[serial_id]
            if serial_id in self.port_configs:
                del self.port_configs[serial_id]
            if serial_id in self.connected_ports:
                port = self.connected_ports.pop(serial_id)
                logger.info(f"Serial port {port} (ID: {serial_id}) disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting serial port {serial_id}: {e}")
    
    async def write_data(self, serial_id: int, data: bytes) -> bool:
        """写入数据到指定串口"""
        connection = self.connections.get(serial_id)
        if not connection or not connection.is_open:
            raise RuntimeError(f"Serial port {serial_id} not connected")
        
        try:
            loop = asyncio.get_event_loop()
            bytes_written = await loop.run_in_executor(
                self.executor, connection.write, data
            )
            
            logger.debug(f"Serial {serial_id}: Written {bytes_written} bytes: {data.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing data to serial {serial_id}: {e}")
            return False
    
    async def read_data(self, serial_id: int, size: int = 1024, timeout: Optional[float] = None) -> bytes:
        """从指定串口读取数据"""
        connection = self.connections.get(serial_id)
        if not connection or not connection.is_open:
            raise RuntimeError(f"Serial port {serial_id} not connected")
        
        try:
            # 设置临时超时
            original_timeout = connection.timeout
            if timeout is not None:
                connection.timeout = timeout
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, lambda: self._read_sync(connection, size)
            )
            
            # 恢复原始超时
            connection.timeout = original_timeout
            
            logger.debug(f"Serial {serial_id}: Read {len(data)} bytes: {data.hex()}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading data from serial {serial_id}: {e}")
            return b""
    
    def _read_sync(self, connection: serial.Serial, size: int) -> bytes:
        """同步读取数据"""
        return connection.read(size)
    
    def _read_until_sync(self, connection: serial.Serial, terminator: bytes, max_size: int = 1024) -> bytes:
        """同步读取数据直到遇到终止符"""
        data = b""
        start_time = time.time()
        timeout = connection.timeout or 1.0
        
        while len(data) < max_size:
            # 检查超时
            if time.time() - start_time > timeout:
                break
                
            # 读取一个字节
            char = connection.read(1)
            if not char:
                break
                
            data += char
            
            # 检查是否遇到终止符
            if terminator in data:
                break
                
        return data
    
    async def read_until(self, serial_id: int, terminator: bytes = b'\r\n', max_size: int = 1024, 
                        timeout: Optional[float] = None) -> bytes:
        """从指定串口读取数据直到遇到指定的终止符"""
        connection = self.connections.get(serial_id)
        if not connection or not connection.is_open:
            raise RuntimeError(f"Serial port {serial_id} not connected")
        
        try:
            # 设置临时超时
            original_timeout = connection.timeout
            if timeout is not None:
                connection.timeout = timeout
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor, lambda: self._read_until_sync(connection, terminator, max_size)
            )
            
            # 恢复原始超时
            connection.timeout = original_timeout
            
            logger.debug(f"Serial {serial_id}: Read until terminator {terminator}: {len(data)} bytes")
            return data
            
        except Exception as e:
            logger.error(f"Error reading until terminator from serial {serial_id}: {e}")
            return b""
    
    async def write_read(self, serial_id: int, data: bytes, read_size: int = 1024, 
                        read_timeout: float = 1.0, write_delay: float = 0.01) -> bytes:
        """写入数据并读取响应（固定大小）"""
        await self.write_data(serial_id, data)
        
        # 给设备一点时间处理命令
        await asyncio.sleep(write_delay)
        
        return await self.read_data(serial_id, read_size, read_timeout)
    
    async def write_read_until(self, serial_id: int, data: bytes, terminator: bytes = b'\r\n', 
                              max_size: int = 1024, read_timeout: float = 1.0, 
                              write_delay: float = 0.01) -> bytes:
        """写入数据并读取响应直到遇到终止符（推荐用于AT命令）"""
        await self.write_data(serial_id, data)
        
        # 给设备一点时间处理命令
        await asyncio.sleep(write_delay)
        
        return await self.read_until(serial_id, terminator, max_size, read_timeout)
    
    def get_connection_info(self, serial_id: int = None) -> Dict[str, Any]:
        """获取连接信息"""
        if serial_id is None:
            # 返回所有连接信息
            return {
                "connected_serials": self.get_connected_serials(),
                "total_connections": len(self.connections)
            }
        
        connection = self.connections.get(serial_id)
        if not connection:
            return {"connected": False, "serial_id": serial_id}
        
        return {
            "connected": connection.is_open,
            "serial_id": serial_id,
            "port": connection.port,
            "baudrate": connection.baudrate,
            "bytesize": connection.bytesize,
            "parity": connection.parity,
            "stopbits": connection.stopbits,
            "timeout": connection.timeout,
        }


# Global serial driver instance
serial_driver = SerialDriver()