"""
WebSocket API路由
提供命令行交互的WebSocket端点
"""

import json
import logging
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, Header, Query
from fastapi.websockets import WebSocketState
from typing import Optional

from app.schemas.websocket import (
    WSCommandMessage, 
    WSResponseMessage, 
    WSErrorMessage, 
    WSMessageType,
    SendMessageRequest,
    SendMessageResponse
)
from app.services.serial_service import serial_service
from app.services.session_service import session_service
from app.core.dependencies import get_session_id_from_header
from app.core.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
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
    
    async def send_message_to_session(self, message: dict):
        """向指定会话发送消息"""
        logger.info(f"当前活跃连接: {list(self.active_connections.keys())}")
        
  
        for websocket in self.active_connections.values():
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        return True

    
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
            
            command_text = data.get("command", "")
            if not command_text:
                error_msg = WSErrorMessage(
                    error="命令不能为空",
                    code=400,
                    timestamp=datetime.now().isoformat()
                )
                await self.send_personal_message(error_msg.model_dump(), websocket)
                return
            
            # 执行AT指令通过串口服务
            try:

                # 直接发送完整的指令字符串到串口
                result = await serial_service.send_at_command(command_text)
                
                # 构造成功响应
                response_msg = WSResponseMessage(
                    type=WSMessageType.RESPONSE,
                    message=result.received_data,
                    data={
                        "sent_data": result.sent_data,
                        "received_data": result.received_data,
                        "timestamp": result.timestamp
                    },
                    timestamp=datetime.now().isoformat(),
                    success=True
                )
                
                await self.send_personal_message(response_msg.model_dump(), websocket)
                
            except Exception as serial_error:
                logger.error(f"串口指令执行失败: {str(serial_error)}")
                error_msg = WSErrorMessage(
                    error=f"指令执行失败: {str(serial_error)}",
                    code=500,
                    timestamp=datetime.now().isoformat()
                )
                await self.send_personal_message(error_msg.model_dump(), websocket)
            
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


@router.websocket("/terminal/{client_id}")
async def websocket_terminal(websocket: WebSocket, client_id: str):
    """
    WebSocket终端端点
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        session_id: 会话ID (可选，用于关联已登录用户)
    """
    logger.info(f"WebSocket连接请求 - client_id: {client_id}")
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


@router.get("/status")
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





@router.post("/send-message", response_model=APIResponse)
async def send_message_to_user(message_request: SendMessageRequest):
    """
    向已登录用户发送WebSocket消息
    
    Args:
        message_request: 消息请求数据
    
    Returns:
        APIResponse: 操作结果
    """
    try:
        # 获取当前活跃会话状态
        session_status = await session_service.get_session_status()
        if not session_status.has_active_session or not session_status.current_session:
            return APIResponse.error(code=404, msg="没有活跃的用户会话")
        
        # 获取目标会话ID（当前系统只支持单用户）
        target_session_id = session_status.current_session.session_id
        
        # 构造WebSocket消息
        ws_message = WSResponseMessage(
            type=message_request.message_type,
            message=message_request.message,
            data=message_request.data,
            timestamp=datetime.now().isoformat(),
            success=True
        )
        
        # 发送消息到WebSocket
        success = await manager.send_message_to_session(
            ws_message.model_dump()
        )
        
        if success:
            return APIResponse.success(
                data=SendMessageResponse(
                    success=True,
                    message="消息发送成功",
                    sent_to_session=target_session_id
                ).model_dump(),
                msg="WebSocket消息发送成功"
            )
        else:
            return APIResponse.error(
                code=500, 
                msg="消息发送失败：目标用户可能未连接WebSocket"
            )
    
    except Exception as e:
        logger.error(f"发送WebSocket消息失败: {str(e)}")
        return APIResponse.error(code=500, msg=f"发送消息失败: {str(e)}")