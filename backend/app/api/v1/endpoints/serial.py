"""
Serial Communication API Endpoints for AT Commands
"""

import logging
from fastapi import APIRouter
from app.core.response import APIResponse
from app.core.exceptions import SerialException, ErrorCode
from app.services.serial_service import serial_service
from app.schemas.serial_schemas import (
    SerialConfig, RawDataRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ports", response_model=APIResponse)
async def get_available_ports():
    """获取可用串口列表"""
    ports = await serial_service.get_available_ports()
    return APIResponse.success(data=ports, msg="获取串口列表成功")


@router.get("/auto-detect", response_model=APIResponse)
async def auto_detect_port():
    """自动检测串口"""
    port = await serial_service.auto_detect_port()
    return APIResponse.success(data={"port": port}, msg="自动检测成功")


@router.post("/connect", response_model=APIResponse)
async def connect_serial(config: SerialConfig):
    """连接串口"""
    await serial_service.connect_serial(config)
    return APIResponse.success(msg="串口连接成功")


@router.post("/disconnect", response_model=APIResponse)
async def disconnect_serial():
    """断开串口连接"""
    await serial_service.disconnect_serial()
    return APIResponse.success(msg="串口断开成功")


@router.get("/status", response_model=APIResponse)
async def get_connection_status():
    """获取串口连接状态"""
    status = await serial_service.get_connection_status()
    return APIResponse.success(data=status, msg="获取状态成功")


@router.post("/send-at", response_model=APIResponse)
async def send_at_command(request: RawDataRequest):
    """发送AT指令"""
    result = await serial_service.send_at_command(request.data)
    return APIResponse.success(data=result, msg="AT指令发送成功")


@router.post("/raw-data", response_model=APIResponse)
async def send_raw_data(request: RawDataRequest):
    """发送原始数据"""
    result = await serial_service.send_raw_data(request.data)
    return APIResponse.success(data=result, msg="发送原始数据成功")