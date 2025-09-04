"""
Commands Management API Endpoints
常用指令管理API端点
"""

import logging
from fastapi import APIRouter, Depends
from typing import Optional, List

from app.core.response import APIResponse
from app.core.dependencies import get_session_id_from_header
from app.services.command_service import command_service
from app.schemas.command_schemas import (
    SavedCommand, 
    CreateCommandRequest, 
    UpdateCommandRequest, 
    CommandsListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=APIResponse[CommandsListResponse])
async def get_all_commands():
    """获取所有常用指令"""
    try:
        commands = await command_service.get_all_commands()
        total = len(commands)
        
        response_data = CommandsListResponse(
            commands=commands,
            total=total
        )
        
        return APIResponse.success(
            data=response_data,
            msg=f"获取到 {total} 条常用指令"
        )
        
    except Exception as e:
        logger.error(f"Error getting all commands: {e}")
        return APIResponse.error(code=500, msg="获取指令列表失败")


@router.post("/", response_model=APIResponse[SavedCommand])
async def create_command(
    request: CreateCommandRequest,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """创建新的常用指令"""
    try:
        # 这里可以添加会话验证，但为了简化，暂时允许任何客户端创建
        
        new_command = await command_service.create_command(request)
        
        if new_command is None:
            return APIResponse.error(code=400, msg="指令名称已存在或创建失败")
        
        return APIResponse.success(
            data=new_command,
            msg="指令创建成功"
        )
        
    except Exception as e:
        logger.error(f"Error creating command: {e}")
        return APIResponse.error(code=500, msg="指令创建失败")


@router.get("/{command_id}", response_model=APIResponse[SavedCommand])
async def get_command(command_id: str):
    """根据ID获取指令详情"""
    try:
        command = await command_service.get_command_by_id(command_id)
        
        if command is None:
            return APIResponse.error(code=404, msg="指令不存在")
        
        return APIResponse.success(
            data=command,
            msg="获取指令成功"
        )
        
    except Exception as e:
        logger.error(f"Error getting command {command_id}: {e}")
        return APIResponse.error(code=500, msg="获取指令失败")


@router.put("/{command_id}", response_model=APIResponse[SavedCommand])
async def update_command(
    command_id: str,
    request: UpdateCommandRequest,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """更新指令"""
    try:
        updated_command = await command_service.update_command(command_id, request)
        
        if updated_command is None:
            return APIResponse.error(code=404, msg="指令不存在或名称冲突")
        
        return APIResponse.success(
            data=updated_command,
            msg="指令更新成功"
        )
        
    except Exception as e:
        logger.error(f"Error updating command {command_id}: {e}")
        return APIResponse.error(code=500, msg="指令更新失败")


@router.delete("/{command_id}", response_model=APIResponse)
async def delete_command(
    command_id: str,
    session_id: Optional[str] = Depends(get_session_id_from_header)
):
    """删除指令"""
    try:
        success = await command_service.delete_command(command_id)
        
        if not success:
            return APIResponse.error(code=404, msg="指令不存在")
        
        return APIResponse.success(
            data=None,
            msg="指令删除成功"
        )
        
    except Exception as e:
        logger.error(f"Error deleting command {command_id}: {e}")
        return APIResponse.error(code=500, msg="指令删除失败")


@router.get("/count/total", response_model=APIResponse[int])
async def get_commands_count():
    """获取指令总数"""
    try:
        count = await command_service.get_commands_count()
        
        return APIResponse.success(
            data=count,
            msg=f"当前共有 {count} 条指令"
        )
        
    except Exception as e:
        logger.error(f"Error getting commands count: {e}")
        return APIResponse.error(code=500, msg="获取指令数量失败")
