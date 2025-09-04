"""
自动化命令API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.schemas.automation import (
    AutomationCommandRequest,
    AutomationCommandResponse,
    CommandConfirmationRequest,
    CommandListResponse,
    CommandTemplate,
    CommandStatus,
    CommandType
)
from app.services.automation_service import automation_service
from app.core.response import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["自动化命令"])


@router.post("/commands", response_model=dict)
async def create_command(request: AutomationCommandRequest):
    """创建自动化命令"""
    try:
        command = await automation_service.create_command(request)
        logger.info(f"API: 创建命令成功 - {command.command_id}")
        return APIResponse.success(data=command.model_dump())
    except Exception as e:
        logger.error(f"API: 创建命令失败 - {e}")
        return APIResponse.error(code=500, msg=f"创建命令失败: {e}")


@router.post("/commands/{command_id}/confirm", response_model=dict)
async def confirm_command(command_id: str, confirmation: CommandConfirmationRequest):
    """确认命令执行"""
    try:
        if confirmation.command_id != command_id:
            raise ValueError("命令ID不匹配")
        
        command = await automation_service.confirm_command(confirmation)
        logger.info(f"API: 命令确认成功 - {command_id}, 确认: {confirmation.confirmed}")
        return APIResponse.success(data=command.model_dump())
    except ValueError as e:
        logger.warning(f"API: 命令确认失败 - {e}")
        return APIResponse.error(code=400, msg=str(e))
    except Exception as e:
        logger.error(f"API: 命令确认异常 - {e}")
        return APIResponse.error(code=500, msg=f"确认命令失败: {e}")


@router.get("/commands/{command_id}", response_model=dict)
async def get_command(command_id: str):
    """获取单个命令信息"""
    try:
        command = automation_service.get_command(command_id)
        if not command:
            return APIResponse.error(code=404, msg="命令不存在")
        
        return APIResponse.success(data=command.model_dump())
    except Exception as e:
        logger.error(f"API: 获取命令失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取命令失败: {e}")


@router.get("/commands", response_model=dict)
async def get_commands(
    status: Optional[CommandStatus] = Query(None, description="命令状态"),
    command_type: Optional[CommandType] = Query(None, description="命令类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """获取命令列表"""
    try:
        result = automation_service.get_commands(
            status=status,
            command_type=command_type,
            page=page,
            page_size=page_size
        )
        
        # 转换为可序列化的格式
        commands_data = []
        for cmd in result["commands"]:
            commands_data.append(cmd.model_dump())
        
        response_data = {
            "commands": commands_data,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        }
        
        return APIResponse.success(data=response_data)
    except Exception as e:
        logger.error(f"API: 获取命令列表失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取命令列表失败: {e}")


@router.delete("/commands/{command_id}", response_model=dict)
async def cancel_command(command_id: str):
    """取消命令执行"""
    try:
        command = await automation_service.cancel_command(command_id)
        logger.info(f"API: 取消命令成功 - {command_id}")
        return APIResponse.success(data=command.model_dump())
    except ValueError as e:
        logger.warning(f"API: 取消命令失败 - {e}")
        return APIResponse.error(code=400, msg=str(e))
    except Exception as e:
        logger.error(f"API: 取消命令异常 - {e}")
        return APIResponse.error(code=500, msg=f"取消命令失败: {e}")


@router.get("/templates", response_model=dict)
async def get_templates():
    """获取命令模板列表"""
    try:
        templates = automation_service.get_templates()
        templates_data = [template.model_dump() for template in templates]
        return APIResponse.success(data=templates_data)
    except Exception as e:
        logger.error(f"API: 获取模板列表失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取模板列表失败: {e}")


@router.get("/templates/{template_id}", response_model=dict)
async def get_template(template_id: str):
    """获取单个命令模板"""
    try:
        template = automation_service.get_template(template_id)
        if not template:
            return APIResponse.error(code=404, msg="模板不存在")
        
        return success_response(data=template.model_dump())
    except Exception as e:
        logger.error(f"API: 获取模板失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取模板失败: {e}")


@router.post("/templates/{template_id}/execute", response_model=dict)
async def execute_template_command(
    template_id: str,
    parameters: dict,
    operator_id: Optional[str] = Query(None, description="操作员ID"),
    workstation_id: Optional[str] = Query(None, description="工位ID")
):
    """根据模板执行命令"""
    try:
        command = await automation_service.execute_template_command(
            template_id=template_id,
            parameters=parameters,
            operator_id=operator_id,
            workstation_id=workstation_id
        )
        
        logger.info(f"API: 模板命令创建成功 - 模板: {template_id}, 命令: {command.command_id}")
        return APIResponse.success(data=command.model_dump())
    except ValueError as e:
        logger.warning(f"API: 模板命令创建失败 - {e}")
        return APIResponse.error(code=400, msg=str(e))
    except Exception as e:
        logger.error(f"API: 模板命令创建异常 - {e}")
        return APIResponse.error(code=500, msg=f"执行模板命令失败: {e}")