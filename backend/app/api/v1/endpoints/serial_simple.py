"""
简化的串口管理API端点
确保返回正确的数据结构，避免undefined值
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def get_connection_status_simple():
    """
    简化的串口连接状态
    """
    try:
        return {
            "code": 0,
            "msg": "获取串口状态成功",
            "data": {
                "connected": False,
                "port": None,
                "baudrate": None,
                "bytesize": None,
                "parity": None,
                "stopbits": None,
                "timeout": None
            }
        }
    except Exception as e:
        logger.error(f"获取串口状态失败: {e}")
        return {
            "code": 500,
            "msg": f"获取串口状态失败: {str(e)}",
            "data": None
        }


@router.get("/ports")
async def get_available_ports_simple():
    """
    简化的可用串口列表
    """
    try:
        # 模拟串口数据，确保所有字段都有值
        mock_ports = [
            {
                "device": "/dev/ttyUSB0",
                "name": "USB Serial Port 0",
                "description": "USB-to-Serial Comm Port",
                "hwid": "USB VID:PID=1234:5678",
                "manufacturer": "FTDI"
            },
            {
                "device": "/dev/ttyUSB1", 
                "name": "USB Serial Port 1",
                "description": "USB-to-Serial Comm Port",
                "hwid": "USB VID:PID=1234:5679",
                "manufacturer": "FTDI"
            },
            {
                "device": "/dev/ttyACM0",
                "name": "Arduino Uno",
                "description": "Arduino USB Serial",
                "hwid": "USB VID:PID=2341:0043",
                "manufacturer": "Arduino"
            }
        ]
        
        return {
            "code": 0,
            "msg": "获取串口列表成功",
            "data": mock_ports
        }
    except Exception as e:
        logger.error(f"获取串口列表失败: {e}")
        return {
            "code": 500,
            "msg": f"获取串口列表失败: {str(e)}",
            "data": []
        }


@router.get("/auto-detect")
async def auto_detect_port_simple():
    """
    简化的自动检测串口
    """
    try:
        # 模拟自动检测结果
        detected_port = "/dev/ttyUSB0"
        
        return {
            "code": 0,
            "msg": "自动检测完成",
            "data": {
                "port": detected_port,
                "confidence": "high",
                "method": "baudrate_test"
            }
        }
    except Exception as e:
        logger.error(f"自动检测失败: {e}")
        return {
            "code": 500,
            "msg": f"自动检测失败: {str(e)}",
            "data": None
        }


@router.post("/connect")
async def connect_serial_simple(config_data: dict):
    """
    简化的串口连接
    """
    try:
        port = config_data.get("port")
        baudrate = config_data.get("baudrate", 115200)
        
        if not port:
            return {
                "code": 400,
                "msg": "缺少串口参数",
                "data": None
            }
        
        # 模拟连接成功
        return {
            "code": 0,
            "msg": "串口连接成功",
            "data": {
                "connected": True,
                "port": port,
                "baudrate": baudrate,
                "bytesize": config_data.get("bytesize", 8),
                "parity": config_data.get("parity", "N"),
                "stopbits": config_data.get("stopbits", 1),
                "timeout": config_data.get("timeout", 0.5)
            }
        }
    except Exception as e:
        logger.error(f"串口连接失败: {e}")
        return {
            "code": 500,
            "msg": f"串口连接失败: {str(e)}",
            "data": None
        }


@router.post("/disconnect")
async def disconnect_serial_simple():
    """
    简化的串口断开
    """
    try:
        return {
            "code": 0,
            "msg": "串口断开成功",
            "data": {
                "connected": False,
                "port": None
            }
        }
    except Exception as e:
        logger.error(f"串口断开失败: {e}")
        return {
            "code": 500,
            "msg": f"串口断开失败: {str(e)}",
            "data": None
        }