"""
TCP连接服务
处理TCP连接的管理和命令发送
"""

import asyncio
import logging
import socket
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from app.schemas.tcp_schemas import TcpConnection, TcpConnectionConfig, TcpCommandRequest, TcpCommandResponse

logger = logging.getLogger(__name__)


class TcpConnectionManager:
    """TCP连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, TcpConnection] = {}
        self.sockets: Dict[str, socket.socket] = {}
        self.lock = asyncio.Lock()
    
    async def create_connection(self, config: TcpConnectionConfig) -> TcpConnection:
        """创建TCP连接"""
        connection_id = str(uuid.uuid4())
        
        try:
            # 创建socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config.timeout)
            
            # 尝试连接
            sock.connect((config.host, config.port))
            
            # 创建连接对象
            connection = TcpConnection(
                id=connection_id,
                host=config.host,
                port=config.port,
                timeout=config.timeout,
                auto_reconnect=config.auto_reconnect,
                connected=True,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            async with self.lock:
                self.connections[connection_id] = connection
                self.sockets[connection_id] = sock
            
            logger.info(f"TCP连接创建成功: {config.host}:{config.port} (ID: {connection_id})")
            return connection
            
        except Exception as e:
            logger.error(f"TCP连接创建失败: {config.host}:{config.port}, 错误: {str(e)}")
            raise Exception(f"TCP连接失败: {str(e)}")
    
    async def disconnect(self, connection_id: str) -> bool:
        """断开TCP连接"""
        try:
            async with self.lock:
                if connection_id in self.connections:
                    connection = self.connections[connection_id]
                    connection.connected = False
                    
                    if connection_id in self.sockets:
                        sock = self.sockets[connection_id]
                        try:
                            sock.close()
                        except:
                            pass
                        del self.sockets[connection_id]
                    
                    logger.info(f"TCP连接断开: {connection.host}:{connection.port} (ID: {connection_id})")
                    return True
                else:
                    logger.warning(f"TCP连接不存在: {connection_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"断开TCP连接失败: {connection_id}, 错误: {str(e)}")
            return False
    
    async def disconnect_all(self) -> int:
        """断开所有TCP连接"""
        disconnected_count = 0
        connection_ids = list(self.connections.keys())
        
        for connection_id in connection_ids:
            if await self.disconnect(connection_id):
                disconnected_count += 1
        
        logger.info(f"已断开所有TCP连接，共 {disconnected_count} 个")
        return disconnected_count
    
    async def get_connection(self, connection_id: str) -> Optional[TcpConnection]:
        """获取TCP连接"""
        return self.connections.get(connection_id)
    
    async def get_all_connections(self) -> List[TcpConnection]:
        """获取所有TCP连接"""
        return list(self.connections.values())
    
    async def send_command(self, request: TcpCommandRequest) -> TcpCommandResponse:
        """发送TCP命令"""
        try:
            connection_id = request.connection_id
            
            if connection_id not in self.connections:
                return TcpCommandResponse(
                    success=False,
                    response=f"TCP连接不存在: {connection_id}"
                )
            
            connection = self.connections[connection_id]
            if not connection.connected:
                return TcpCommandResponse(
                    success=False,
                    response=f"TCP连接未连接: {connection.host}:{connection.port}"
                )
            
            if connection_id not in self.sockets:
                return TcpCommandResponse(
                    success=False,
                    response=f"TCP socket不存在: {connection_id}"
                )
            
            sock = self.sockets[connection_id]
            
            # 准备命令
            command = request.command
            if request.auto_add_crlf and not command.endswith('\r\n'):
                command += '\r\n'
            
            # 清理缓冲区（读取所有可用数据）
            try:
                sock.settimeout(0.1)  # 设置短超时
                while True:
                    data = sock.recv(1024)
                    if not data:
                        break
            except socket.timeout:
                pass  # 没有更多数据
            except Exception as e:
                logger.warning(f"清理缓冲区时出错: {str(e)}")
            
            # 发送命令
            sock.settimeout(connection.timeout)
            sock.send(command.encode('utf-8'))
            
            # 等待响应
            await asyncio.sleep(0.1)  # 等待设备处理
            
            # 接收响应
            response_data = sock.recv(4096)
            response = response_data.decode('utf-8', errors='ignore')
            
            # 更新最后活动时间
            connection.last_activity = datetime.now()
            
            logger.info(f"TCP命令发送成功: {connection.host}:{connection.port}, 命令: {command.strip()}, 响应: {response.strip()}")
            
            return TcpCommandResponse(
                success=True,
                response=response
            )
            
        except Exception as e:
            logger.error(f"发送TCP命令失败: {str(e)}")
            return TcpCommandResponse(
                success=False,
                response=f"发送命令失败: {str(e)}"
            )
    
    async def check_connection_health(self, connection_id: str) -> bool:
        """检查连接健康状态"""
        try:
            if connection_id not in self.connections or connection_id not in self.sockets:
                return False
            
            connection = self.connections[connection_id]
            sock = self.sockets[connection_id]
            
            # 尝试发送一个简单的ping命令
            sock.settimeout(1)
            sock.send(b'\r\n')  # 发送空行
            
            # 尝试接收响应
            try:
                response = sock.recv(1024)
                connection.last_activity = datetime.now()
                return True
            except socket.timeout:
                return False
                
        except Exception as e:
            logger.warning(f"检查TCP连接健康状态失败: {connection_id}, 错误: {str(e)}")
            return False
    
    async def cleanup_disconnected(self):
        """清理断开的连接"""
        disconnected_ids = []
        
        for connection_id, connection in self.connections.items():
            if not connection.connected or not await self.check_connection_health(connection_id):
                disconnected_ids.append(connection_id)
        
        for connection_id in disconnected_ids:
            await self.disconnect(connection_id)
        
        if disconnected_ids:
            logger.info(f"清理了 {len(disconnected_ids)} 个断开的TCP连接")


# 全局TCP连接管理器实例
tcp_manager = TcpConnectionManager()