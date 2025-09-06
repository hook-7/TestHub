"""
Serial Communication API Endpoints for AT Commands
"""

import logging
from fastapi import APIRouter, Request, Depends, status
from typing import Optional

from app.core.response import APIResponse
from app.core.dependencies import validate_session_dependency
from app.services.serial_service import serial_service
from app.schemas.serial_schemas import (
    SerialConfig, RawDataRequest, SerialConnectRequest, SerialConnectResponse, SerialDisconnectRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/ports", 
    response_model=APIResponse, 
    status_code=status.HTTP_200_OK,
    summary="获取可用串口列表",
    description="扫描系统中所有可用的串口设备，返回详细的设备信息",
    tags=["串口管理"]
)
async def get_available_ports():
    """获取可用串口列表"""
    ports = await serial_service.get_available_ports()
    return APIResponse.success(data=ports, msg="获取串口列表成功")


@router.get("/auto-detect", response_model=APIResponse)
async def auto_detect_port():
    """自动检测串口"""
    port = await serial_service.auto_detect_port()
    return APIResponse.success(data={"port": port}, msg="自动检测成功")


@router.post("/connect", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def connect_serial(
    config: SerialConfig,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """连接串口（需要有效会话）"""
    serial_id = await serial_service.connect_serial(config)
    logger.info(f"Serial connected by session: {session_id}, assigned serial_id: {serial_id}")
    
    response_data = SerialConnectResponse(
        serial_id=serial_id,
        port=config.port,
        message=f"串口连接成功，分配ID: {serial_id}"
    )
    return APIResponse.success(data=response_data, msg="串口连接成功")


@router.post("/disconnect", response_model=APIResponse)
async def disconnect_serial(
    disconnect_request: SerialDisconnectRequest,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """断开串口连接（需要有效会话）"""
    await serial_service.disconnect_serial(disconnect_request.serial_id)
    if disconnect_request.serial_id is None:
        logger.info(f"All serials disconnected by session: {session_id}")
        return APIResponse.success(msg="所有串口断开成功")
    else:
        logger.info(f"Serial {disconnect_request.serial_id} disconnected by session: {session_id}")
        return APIResponse.success(msg=f"串口 {disconnect_request.serial_id} 断开成功")


@router.get("/status", response_model=APIResponse)
async def get_connection_status():
    """获取串口连接状态"""
    status = await serial_service.get_connection_status()
    return APIResponse.success(data=status, msg="获取状态成功")


@router.post("/send-at", response_model=APIResponse)
async def send_at_command(
    request_data: RawDataRequest,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """发送指令（支持AT指令和其他自定义指令）（需要有效会话）"""
    result = await serial_service.send_at_command(request_data.data, request_data.serial_id)
    return APIResponse.success(data=result, msg="指令发送成功")


@router.post("/raw-data", response_model=APIResponse)
async def send_raw_data(
    request_data: RawDataRequest,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """发送原始数据（需要有效会话）"""
    result = await serial_service.send_raw_data(request_data.data, request_data.serial_id)
    return APIResponse.success(data=result, msg="发送原始数据成功")