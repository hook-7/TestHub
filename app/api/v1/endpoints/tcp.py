"""
TCP连接管理API端点
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List

from app.core.response import APIResponse
from app.services.tcp_service import tcp_manager
from app.schemas.tcp_schemas import (
    TcpConnectionConfig,
    TcpConnection,
    TcpCommandRequest,
    TcpCommandResponse,
    TcpConnectionsListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/connect", response_model=APIResponse[TcpConnection])
async def create_tcp_connection(config: TcpConnectionConfig):
    """创建TCP连接"""
    try:
        connection = await tcp_manager.create_connection(config)
        
        return APIResponse.success(
            data=connection,
            msg=f"TCP连接创建成功: {config.host}:{config.port}"
        )
        
    except Exception as e:
        logger.error(f"创建TCP连接失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg=f"TCP连接创建失败: {str(e)}"
        )


@router.get("/connections", response_model=APIResponse[TcpConnectionsListResponse])
async def get_tcp_connections():
    """获取所有TCP连接"""
    try:
        connections = await tcp_manager.get_all_connections()
        
        response_data = TcpConnectionsListResponse(
            connections=connections,
            total=len(connections)
        )
        
        return APIResponse.success(
            data=response_data,
            msg=f"获取到 {len(connections)} 个TCP连接"
        )
        
    except Exception as e:
        logger.error(f"获取TCP连接列表失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg="获取TCP连接列表失败"
        )


@router.get("/connections/{connection_id}", response_model=APIResponse[TcpConnection])
async def get_tcp_connection(connection_id: str):
    """获取指定TCP连接"""
    try:
        connection = await tcp_manager.get_connection(connection_id)
        
        if not connection:
            return APIResponse.error(
                code=404,
                msg="TCP连接不存在"
            )
        
        return APIResponse.success(
            data=connection,
            msg="获取TCP连接成功"
        )
        
    except Exception as e:
        logger.error(f"获取TCP连接失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg="获取TCP连接失败"
        )


@router.delete("/connections/{connection_id}", response_model=APIResponse)
async def disconnect_tcp(connection_id: str):
    """断开TCP连接"""
    try:
        success = await tcp_manager.disconnect(connection_id)
        
        if not success:
            return APIResponse.error(
                code=404,
                msg="TCP连接不存在"
            )
        
        return APIResponse.success(
            data=None,
            msg="TCP连接断开成功"
        )
        
    except Exception as e:
        logger.error(f"断开TCP连接失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg="断开TCP连接失败"
        )


@router.delete("/connections", response_model=APIResponse)
async def disconnect_all_tcp():
    """断开所有TCP连接"""
    try:
        disconnected_count = await tcp_manager.disconnect_all()
        
        return APIResponse.success(
            data={"disconnected_count": disconnected_count},
            msg=f"成功断开 {disconnected_count} 个TCP连接"
        )
        
    except Exception as e:
        logger.error(f"断开所有TCP连接失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg="断开所有TCP连接失败"
        )


@router.post("/send-command", response_model=APIResponse[TcpCommandResponse])
async def send_tcp_command(request: TcpCommandRequest):
    """发送TCP命令"""
    try:
        response = await tcp_manager.send_command(request)
        
        if response.success:
            return APIResponse.success(
                data=response,
                msg="TCP命令发送成功"
            )
        else:
            return APIResponse.error(
                code=400,
                msg=f"TCP命令发送失败: {response.response}"
            )
        
    except Exception as e:
        logger.error(f"发送TCP命令失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg=f"发送TCP命令失败: {str(e)}"
        )


@router.get("/connections/{connection_id}/health", response_model=APIResponse[bool])
async def check_tcp_connection_health(connection_id: str):
    """检查TCP连接健康状态"""
    try:
        is_healthy = await tcp_manager.check_connection_health(connection_id)
        
        return APIResponse.success(
            data=is_healthy,
            msg="TCP连接健康检查完成"
        )
        
    except Exception as e:
        logger.error(f"检查TCP连接健康状态失败: {str(e)}")
        return APIResponse.error(
            code=500,
            msg="检查TCP连接健康状态失败"
        )