"""
WebSocket API路由
提供命令行交互的WebSocket端点
"""

import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.schemas.websocket import (
    WSCommandMessage, 
    WSResponseMessage, 
    WSErrorMessage, 
    WSMessageType
)
from app.services.command_service import CommandService

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.command_service = CommandService()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket客户端连接: {client_id}")
        
        # 发送欢迎消息
        welcome_msg = WSResponseMessage(
            type=WSMessageType.INFO,
            message="欢迎使用Industrial HMI命令行界面！\n输入 'help' 查看可用命令。",
            timestamp=datetime.now().isoformat(),
            success=True
        )
        await self.send_personal_message(welcome_msg.model_dump(), websocket)
    
    def disconnect(self, client_id: str):
        """断开WebSocket连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket客户端断开: {client_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接的客户端"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                else:
                    disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"广播消息给客户端 {client_id} 失败: {str(e)}")
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def handle_command(self, websocket: WebSocket, data: dict):
        """处理命令消息"""
        try:
            # 解析命令消息
            if data.get("type") != WSMessageType.COMMAND:
                error_msg = WSErrorMessage(
                    error="无效的消息类型",
                    code=400,
                    timestamp=datetime.now().isoformat()
                )
                await self.send_personal_message(error_msg.model_dump(), websocket)
                return
            
            command_text = data.get("command", "").strip()
            if not command_text:
                error_msg = WSErrorMessage(
                    error="命令不能为空",
                    code=400,
                    timestamp=datetime.now().isoformat()
                )
                await self.send_personal_message(error_msg.model_dump(), websocket)
                return
            
            # 解析命令和参数
            parts = command_text.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # 执行命令
            response = await self.command_service.execute_command(command, args)
            await self.send_personal_message(response.model_dump(), websocket)
            
        except Exception as e:
            logger.error(f"处理命令失败: {str(e)}")
            error_msg = WSErrorMessage(
                error=f"处理命令失败: {str(e)}",
                code=500,
                timestamp=datetime.now().isoformat()
            )
            await self.send_personal_message(error_msg.model_dump(), websocket)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/terminal/{client_id}")
async def websocket_terminal(websocket: WebSocket, client_id: str):
    """
    WebSocket终端端点
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                # 解析JSON消息
                message_data = json.loads(data)
                logger.debug(f"收到WebSocket消息: {message_data}")
                
                # 处理命令
                await manager.handle_command(websocket, message_data)
                
            except json.JSONDecodeError:
                error_msg = WSErrorMessage(
                    error="无效的JSON格式",
                    code=400,
                    timestamp=datetime.now().isoformat()
                )
                await manager.send_personal_message(error_msg.model_dump(), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"WebSocket客户端 {client_id} 主动断开连接")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        manager.disconnect(client_id)


@router.get("/ws/status")
async def websocket_status():
    """获取WebSocket连接状态"""
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "active_connections": len(manager.active_connections),
            "connected_clients": list(manager.active_connections.keys())
        }
    }