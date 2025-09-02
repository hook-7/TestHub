"""
Serial Communication API Endpoints for AT Commands
"""

import logging
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from typing import Optional

from app.core.response import APIResponse
from app.core.exceptions import SerialException, SessionException, ErrorCode
from app.services.serial_service import serial_service
from app.services.session_service import session_service
from app.schemas.serial_schemas import (
    SerialConfig, RawDataRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_session_id_from_header(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
    """从请求头获取会话ID"""
    return x_session_id


async def validate_session_dependency(
    request: Request,
    session_id: Optional[str] = Depends(get_session_id_from_header)
) -> str:
    """会话验证依赖"""
    if not session_id:
        raise HTTPException(status_code=401, detail="缺少会话ID，请先登录")
    
    is_valid = await session_service.validate_session(session_id, request)
    if not is_valid:
        raise HTTPException(status_code=401, detail="会话无效或已过期，请重新登录")
    
    return session_id


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


@router.post("/connect-and-login", response_model=APIResponse)
async def connect_serial_and_login(
    config: SerialConfig,
    request: Request
):
    """连接串口并自动登录"""
    try:
        # 首先尝试连接串口
        await serial_service.connect_serial(config)
        
        # 串口连接成功后，创建会话（登录）
        session_response = await session_service.create_session_with_serial_auth(request)
        
        logger.info(f"Serial connected and logged in: {session_response.session_id}")
        
        return APIResponse.success(
            data={
                "session_id": session_response.session_id,
                "token": session_response.token,
                "expires_in": session_response.expires_in,
                "serial_connected": True
            },
            msg="串口连接并登录成功"
        )
        
    except Exception as e:
        # 如果登录失败，断开串口连接
        try:
            await serial_service.disconnect_serial()
        except:
            pass
        raise

@router.post("/connect", response_model=APIResponse)
async def connect_serial(
    config: SerialConfig,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """连接串口（需要有效会话）"""
    await serial_service.connect_serial(config)
    logger.info(f"Serial connected by session: {session_id}")
    return APIResponse.success(msg="串口连接成功")


@router.post("/disconnect", response_model=APIResponse)
async def disconnect_serial(
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """断开串口连接（需要有效会话）"""
    await serial_service.disconnect_serial()
    logger.info(f"Serial disconnected by session: {session_id}")
    return APIResponse.success(msg="串口断开成功")


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
    result = await serial_service.send_at_command(request_data.data)
    return APIResponse.success(data=result, msg="指令发送成功")


@router.post("/raw-data", response_model=APIResponse)
async def send_raw_data(
    request_data: RawDataRequest,
    request: Request,
    session_id: str = Depends(validate_session_dependency)
):
    """发送原始数据（需要有效会话）"""
    result = await serial_service.send_raw_data(request_data.data)
    return APIResponse.success(data=result, msg="发送原始数据成功")