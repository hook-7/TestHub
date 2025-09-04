"""
工作流管理API端点
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.core.response import create_response, ErrorCode
from app.core.exceptions import ValidationError, WorkflowError
from app.services.workflow_service import get_workflow_service, WorkflowService
from app.schemas.workflow_schemas import (
    WorkflowDefinition, WorkflowExecution, WorkflowExecutionStatus,
    WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowExecuteRequest,
    WorkflowExecutionResponse, WorkflowConfirmRequest,
    WorkflowListResponse, WorkflowExecutionListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=WorkflowDefinition, tags=["工作流管理"])
async def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    创建新的工作流
    
    - **name**: 工作流名称
    - **description**: 工作流描述（可选）
    - **variables**: 初始变量字典（可选）
    - **steps**: 工作流步骤定义列表
    """
    try:
        workflow_data = request.model_dump()
        workflow = workflow_service.create_workflow(workflow_data)
        
        return create_response(
            data=workflow,
            message="工作流创建成功"
        )
    
    except ValidationError as e:
        logger.error(f"工作流创建验证失败: {e}")
        return create_response(
            code=ErrorCode.PARAM_ERROR,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"工作流创建失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="工作流创建失败"
        )


@router.get("/", response_model=WorkflowListResponse, tags=["工作流管理"])
async def list_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    获取所有工作流列表
    """
    try:
        workflows = workflow_service.list_workflows()
        
        return create_response(
            data={
                "workflows": workflows,
                "total": len(workflows)
            },
            message="获取工作流列表成功"
        )
    
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="获取工作流列表失败"
        )


@router.get("/{workflow_id}", response_model=WorkflowDefinition, tags=["工作流管理"])
async def get_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    获取指定工作流详情
    """
    try:
        workflow = workflow_service.get_workflow(workflow_id)
        if not workflow:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="工作流不存在"
            )
        
        return create_response(
            data=workflow,
            message="获取工作流详情成功"
        )
    
    except Exception as e:
        logger.error(f"获取工作流详情失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="获取工作流详情失败"
        )


@router.put("/{workflow_id}", response_model=WorkflowDefinition, tags=["工作流管理"])
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    更新工作流
    """
    try:
        update_data = request.model_dump(exclude_unset=True)
        workflow = workflow_service.update_workflow(workflow_id, update_data)
        
        if not workflow:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="工作流不存在"
            )
        
        return create_response(
            data=workflow,
            message="工作流更新成功"
        )
    
    except ValidationError as e:
        logger.error(f"工作流更新验证失败: {e}")
        return create_response(
            code=ErrorCode.PARAM_ERROR,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"工作流更新失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="工作流更新失败"
        )


@router.delete("/{workflow_id}", tags=["工作流管理"])
async def delete_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    删除工作流
    """
    try:
        success = workflow_service.delete_workflow(workflow_id)
        
        if not success:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="工作流不存在"
            )
        
        return create_response(
            message="工作流删除成功"
        )
    
    except Exception as e:
        logger.error(f"工作流删除失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="工作流删除失败"
        )


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse, tags=["工作流执行"])
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    执行工作流
    
    - **variables**: 执行时的变量覆盖（可选）
    - **session_id**: 关联的会话ID（可选）
    """
    try:
        execution_id = await workflow_service.execute_workflow(
            workflow_id, 
            request.variables, 
            request.session_id
        )
        
        return create_response(
            data={
                "execution_id": execution_id,
                "status": WorkflowExecutionStatus.RUNNING,
                "message": "工作流开始执行"
            },
            message="工作流执行启动成功"
        )
    
    except ValidationError as e:
        logger.error(f"工作流执行验证失败: {e}")
        return create_response(
            code=ErrorCode.WORKFLOW_NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"工作流执行启动失败: {e}")
        return create_response(
            code=ErrorCode.WORKFLOW_EXECUTION_FAILED,
            message="工作流执行启动失败"
        )


@router.get("/execution/{execution_id}", response_model=WorkflowExecution, tags=["工作流执行"])
async def get_execution_status(
    execution_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    获取工作流执行状态
    """
    try:
        execution = workflow_service.get_execution(execution_id)
        if not execution:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="执行实例不存在"
            )
        
        return create_response(
            data=execution,
            message="获取执行状态成功"
        )
    
    except Exception as e:
        logger.error(f"获取执行状态失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="获取执行状态失败"
        )


@router.post("/execution/{execution_id}/confirm", tags=["工作流执行"])
async def confirm_workflow_step(
    execution_id: str,
    request: WorkflowConfirmRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    确认工作流步骤
    """
    try:
        success = workflow_service.handle_confirm_response(
            request.execution_id, 
            request.action
        )
        
        if not success:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="执行实例不存在或不在等待确认状态"
            )
        
        return create_response(
            message="确认操作成功"
        )
    
    except Exception as e:
        logger.error(f"确认操作失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="确认操作失败"
        )


@router.post("/execution/{execution_id}/cancel", tags=["工作流执行"])
async def cancel_workflow_execution(
    execution_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    取消工作流执行
    """
    try:
        success = workflow_service.cancel_execution(execution_id)
        
        if not success:
            return create_response(
                code=ErrorCode.WORKFLOW_NOT_FOUND,
                message="执行实例不存在"
            )
        
        return create_response(
            message="工作流执行已取消"
        )
    
    except Exception as e:
        logger.error(f"取消工作流执行失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="取消工作流执行失败"
        )


@router.get("/executions", response_model=WorkflowExecutionListResponse, tags=["工作流执行"])
async def list_executions(
    status: Optional[WorkflowExecutionStatus] = Query(None, description="按状态筛选"),
    limit: int = Query(50, description="返回数量限制"),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    获取工作流执行列表
    """
    try:
        executions = workflow_service.list_executions()
        
        # 状态筛选
        if status:
            executions = [e for e in executions if e.status == status]
        
        # 分页
        executions = executions[:limit]
        
        return create_response(
            data={
                "executions": executions,
                "total": len(executions)
            },
            message="获取执行列表成功"
        )
    
    except Exception as e:
        logger.error(f"获取执行列表失败: {e}")
        return create_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="获取执行列表失败"
        )