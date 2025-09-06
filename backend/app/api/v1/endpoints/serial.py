"""
Serial Communication API Endpoints for AT Commands
"""

import logging
from fastapi import APIRouter, Request, Depends, status
from typing import Optional

from app.core.response import APIResponse
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
    request: Request
):
    """连接串口"""
    serial_id = await serial_service.connect_serial(config)
    logger.info(f"Serial connected, assigned serial_id: {serial_id}")
    
    response_data = SerialConnectResponse(
        serial_id=serial_id,
        port=config.port,
        message=f"串口连接成功，分配ID: {serial_id}"
    )
    return APIResponse.success(data=response_data, msg="串口连接成功")


@router.post("/disconnect", response_model=APIResponse)
async def disconnect_serial(
    disconnect_request: SerialDisconnectRequest,
    request: Request
):
    """断开串口连接"""
    await serial_service.disconnect_serial(disconnect_request.serial_id)
    if disconnect_request.serial_id is None:
        logger.info("All serials disconnected")
        return APIResponse.success(msg="所有串口断开成功")
    else:
        logger.info(f"Serial {disconnect_request.serial_id} disconnected")
        return APIResponse.success(msg=f"串口 {disconnect_request.serial_id} 断开成功")


@router.get("/status", response_model=APIResponse)
async def get_connection_status():
    """获取串口连接状态"""
    status = await serial_service.get_connection_status()
    return APIResponse.success(data=status, msg="获取状态成功")


@router.post("/send-at", response_model=APIResponse)
async def send_at_command(
    request_data: RawDataRequest,
    request: Request
):
    """发送指令（支持AT指令和其他自定义指令）- 模拟返回期望值内容"""
    import time
    
    # 注释掉原有的服务调用
    result = await serial_service.send_at_command(request_data.data, request_data.serial_id)
    
    # 模拟返回期望值内容
    # def get_mock_response(command: str) -> str:
    #     """根据命令返回模拟的期望响应"""
    #     # 模拟响应映射表
    #     mock_responses = {
    #         # MAC相关命令
    #         "AT+MAC=026501123456": "OK\r\n",
    #         "AT+MAC?": "026501123456\r\nOK\r\n",
            
    #         # 测试命令
    #         "Eeprom": "EEPROM Test OK\r\n",
    #         "ON1": "LED1OK\r\n",
    #         "ON2": "LED2OK\r\n", 
    #         "ON3": "LED3OK\r\n",
    #         "DPLCA": "DPLCA OK\r\n",
    #         "S485B": "485BOK\r\n",
            
    #         # 通用AT命令
    #         "AT": "OK\r\n",
    #         "AT+GMR": "SIM800L_V1.0.0\r\nOK\r\n",
    #         "AT+CGMI": "SIMCOM_Ltd\r\nOK\r\n",
    #         "AT+CGMM": "SIM800L\r\nOK\r\n",
    #         "AT+CGMR": "SIM800L_V1.0.0\r\nOK\r\n",
    #         "AT+CGSN": "123456789012345\r\nOK\r\n",
    #         "AT+CSQ": "+CSQ: 20,99\r\nOK\r\n",
    #         "AT+CREG?": "+CREG: 0,1\r\nOK\r\n",
    #         "AT+COPS?": "+COPS: 0,0,\"China Mobile\"\r\nOK\r\n",
    #     }
        
    #     # 清理命令，移除可能的\r\n
    #     clean_command = command.strip()
        
    #     # 直接匹配
    #     if clean_command in mock_responses:
    #         return mock_responses[clean_command]
        
    #     # 模糊匹配 - 检查命令是否包含特定关键词
    #     if "MAC=" in clean_command:
    #         return "OK\r\n"
    #     elif "MAC?" in clean_command:
    #         # 提取MAC地址并返回
    #         if "=" in clean_command:
    #             mac = clean_command.split("=")[1]
    #             return f"{mac}\r\nOK\r\n"
    #         else:
    #             return "026501123456\r\nOK\r\n"
    #     elif "LED" in clean_command.upper():
    #         return "LED OK\r\n"
    #     elif "TEST" in clean_command.upper():
    #         return "Test OK\r\n"
    #     elif clean_command.startswith("AT+"):
    #         return "OK\r\n"
    #     else:
    #         # 默认响应
    #         return "OK\r\n"
    
    # # 生成模拟响应
    # mock_response = get_mock_response(request_data.data)
    # serial_id = request_data.serial_id or 1
    
    # # 创建模拟的RawDataResponse
    # from app.schemas.serial_schemas import RawDataResponse
    # result = RawDataResponse(
    #     serial_id=serial_id,
    #     sent_data=request_data.data,
    #     received_data=mock_response,
    #     timestamp=time.time()
    # )
    
    return APIResponse.success(data=result, msg="指令发送成功")


@router.post("/raw-data", response_model=APIResponse)
async def send_raw_data(
    request_data: RawDataRequest,
    request: Request
):
    """发送原始数据"""
    result = await serial_service.send_raw_data(request_data.data, request_data.serial_id)
    return APIResponse.success(data=result, msg="发送原始数据成功")