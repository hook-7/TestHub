"""
Serial Communication API Endpoints
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from app.core.response import APIResponse
from app.services.serial_service import serial_service
from app.schemas.serial_schemas import (
    SerialPortInfo, SerialConfig, SerialConnectionStatus,
    ReadRegistersRequest, WriteRegisterRequest, WriteRegistersRequest,
    ReadRegistersResponse, WriteResponse, RawDataRequest, RawDataResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ports", response_model=APIResponse)
async def get_available_ports():
    """获取可用串口列表"""
    try:
        ports = await serial_service.get_available_ports()
        return APIResponse.success(data=ports, msg="获取串口列表成功")
    except Exception as e:
        logger.error(f"Error getting ports: {e}")
        return APIResponse.system_error("获取串口列表失败")


@router.get("/auto-detect", response_model=APIResponse)
async def auto_detect_port():
    """自动检测串口"""
    try:
        port = await serial_service.auto_detect_port()
        if port:
            return APIResponse.success(data={"port": port}, msg="自动检测成功")
        else:
            return APIResponse.business_error(1, "未检测到可用串口")
    except Exception as e:
        logger.error(f"Error auto-detecting port: {e}")
        return APIResponse.system_error("自动检测失败")


@router.post("/connect", response_model=APIResponse)
async def connect_serial(config: SerialConfig):
    """连接串口"""
    try:
        success = await serial_service.connect_serial(config)
        if success:
            return APIResponse.success(msg="串口连接成功")
        else:
            return APIResponse.business_error(2, "串口连接失败")
    except Exception as e:
        logger.error(f"Error connecting serial: {e}")
        return APIResponse.system_error("串口连接异常")


@router.post("/disconnect", response_model=APIResponse)
async def disconnect_serial():
    """断开串口连接"""
    try:
        success = await serial_service.disconnect_serial()
        if success:
            return APIResponse.success(msg="串口断开成功")
        else:
            return APIResponse.business_error(3, "串口断开失败")
    except Exception as e:
        logger.error(f"Error disconnecting serial: {e}")
        return APIResponse.system_error("串口断开异常")


@router.get("/status", response_model=APIResponse)
async def get_connection_status():
    """获取串口连接状态"""
    try:
        status = await serial_service.get_connection_status()
        return APIResponse.success(data=status, msg="获取状态成功")
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return APIResponse.system_error("获取状态失败")


@router.post("/read-registers", response_model=APIResponse)
async def read_registers(request: ReadRegistersRequest):
    """读取寄存器"""
    try:
        result = await serial_service.read_registers(request)
        if result:
            return APIResponse.success(data=result, msg="读取寄存器成功")
        else:
            return APIResponse.business_error(4, "读取寄存器失败")
    except Exception as e:
        logger.error(f"Error reading registers: {e}")
        return APIResponse.system_error("读取寄存器异常")


@router.post("/write-register", response_model=APIResponse)
async def write_register(request: WriteRegisterRequest):
    """写入单个寄存器"""
    try:
        result = await serial_service.write_register(request)
        return APIResponse.success(data=result, msg="写入操作完成")
    except Exception as e:
        logger.error(f"Error writing register: {e}")
        return APIResponse.system_error("写入寄存器异常")


@router.post("/write-registers", response_model=APIResponse)
async def write_registers(request: WriteRegistersRequest):
    """写入多个寄存器"""
    try:
        result = await serial_service.write_registers(request)
        return APIResponse.success(data=result, msg="批量写入操作完成")
    except Exception as e:
        logger.error(f"Error writing registers: {e}")
        return APIResponse.system_error("批量写入寄存器异常")


@router.post("/raw-data", response_model=APIResponse)
async def send_raw_data(request: RawDataRequest):
    """发送原始数据"""
    try:
        result = await serial_service.send_raw_data(request.data)
        return APIResponse.success(data=result, msg="发送原始数据成功")
    except ValueError as e:
        return APIResponse.param_error(str(e))
    except RuntimeError as e:
        return APIResponse.business_error(5, str(e))
    except Exception as e:
        logger.error(f"Error sending raw data: {e}")
        return APIResponse.system_error("发送原始数据异常")