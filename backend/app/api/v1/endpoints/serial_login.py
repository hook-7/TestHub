"""
Serial Login Configuration API Endpoints
串口登录配置API端点
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional

from app.core.response import APIResponse
from app.core.exceptions import SerialException, ErrorCode
from app.services.serial_login_service import serial_login_service
from app.schemas.serial_login_schemas import (
    CreateSerialLoginConfigRequest,
    UpdateSerialLoginConfigRequest,
    SerialLoginTestRequest,
    SerialLoginConfigResponse,
    SerialLoginTestResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/configs", response_model=APIResponse[List[SerialLoginConfigResponse]])
async def get_serial_login_configs():
    """获取所有串口登录配置"""
    try:
        configs = await serial_login_service.get_all_configs()
        return APIResponse.success(data=configs, msg="获取配置列表成功")
    except Exception as e:
        logger.error(f"获取串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"获取配置失败: {str(e)}")


@router.get("/configs/{config_id}", response_model=APIResponse[SerialLoginConfigResponse])
async def get_serial_login_config(config_id: int):
    """获取指定串口登录配置"""
    try:
        config = await serial_login_service.get_config_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        return APIResponse.success(data=config, msg="获取配置成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"获取配置失败: {str(e)}")


@router.post("/configs", response_model=APIResponse[SerialLoginConfigResponse])
async def create_serial_login_config(config_request: CreateSerialLoginConfigRequest):
    """创建新的串口登录配置"""
    try:
        config = await serial_login_service.create_config(config_request)
        return APIResponse.success(data=config, msg="创建配置成功")
    except SerialException as e:
        return APIResponse.error(code=e.error_code, msg=str(e))
    except Exception as e:
        logger.error(f"创建串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"创建配置失败: {str(e)}")


@router.put("/configs/{config_id}", response_model=APIResponse[SerialLoginConfigResponse])
async def update_serial_login_config(config_id: int, config_request: UpdateSerialLoginConfigRequest):
    """更新串口登录配置"""
    try:
        config = await serial_login_service.update_config(config_id, config_request)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        return APIResponse.success(data=config, msg="更新配置成功")
    except HTTPException:
        raise
    except SerialException as e:
        return APIResponse.error(code=e.error_code, msg=str(e))
    except Exception as e:
        logger.error(f"更新串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"更新配置失败: {str(e)}")


@router.delete("/configs/{config_id}", response_model=APIResponse)
async def delete_serial_login_config(config_id: int):
    """删除串口登录配置"""
    try:
        success = await serial_login_service.delete_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return APIResponse.success(msg="删除配置成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"删除配置失败: {str(e)}")


@router.post("/configs/{config_id}/activate", response_model=APIResponse)
async def activate_serial_login_config(config_id: int):
    """激活指定的串口登录配置"""
    try:
        success = await serial_login_service.activate_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return APIResponse.success(msg="配置激活成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"激活配置失败: {str(e)}")


@router.post("/test", response_model=APIResponse[SerialLoginTestResponse])
async def test_serial_login(test_request: SerialLoginTestRequest):
    """测试串口登录配置"""
    try:
        test_result = await serial_login_service.test_config(test_request)
        return APIResponse.success(data=test_result, msg="测试完成")
    except SerialException as e:
        return APIResponse.error(code=e.error_code, msg=str(e))
    except Exception as e:
        logger.error(f"测试串口登录配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"测试失败: {str(e)}")


@router.post("/connect", response_model=APIResponse)
async def connect_with_active_config():
    """使用当前激活的配置连接串口"""
    try:
        success = await serial_login_service.connect_with_active_config()
        if not success:
            return APIResponse.error(code=ErrorCode.BUSINESS_ERROR, msg="没有激活的配置或连接失败")
        return APIResponse.success(msg="连接成功")
    except SerialException as e:
        return APIResponse.error(code=e.error_code, msg=str(e))
    except Exception as e:
        logger.error(f"使用激活配置连接失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"连接失败: {str(e)}")


@router.get("/active-config", response_model=APIResponse[Optional[SerialLoginConfigResponse]])
async def get_active_config():
    """获取当前激活的串口登录配置"""
    try:
        config = await serial_login_service.get_active_config()
        return APIResponse.success(data=config, msg="获取激活配置成功")
    except Exception as e:
        logger.error(f"获取激活配置失败: {e}")
        return APIResponse.error(code=ErrorCode.SYSTEM_ERROR, msg=f"获取激活配置失败: {str(e)}")