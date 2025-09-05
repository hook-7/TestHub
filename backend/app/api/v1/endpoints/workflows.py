"""
Workflow API endpoints
批量作业工作流管理API端点
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from app.schemas.workflow_schemas import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    BatchWorkflow,
    WorkflowsListResponse,
    WorkflowExecutionStatus,
    ExecuteWorkflowRequest,
    ExecuteWorkflowResponse
)
from app.schemas.common import APIResponse
from app.services.workflow_service import workflow_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=APIResponse[WorkflowsListResponse])
async def get_all_workflows():
    """获取所有工作流"""
    try:
        workflows = await workflow_service.get_all_workflows()
        total = len(workflows)
        
        response_data = WorkflowsListResponse(
            workflows=workflows,
            total=total
        )
        
        return APIResponse(
            code=0,
            msg=f"获取到 {total} 个工作流",
            data=response_data
        )
    except Exception as e:
        logger.error(f"Error getting all workflows: {e}")
        raise HTTPException(status_code=500, detail="获取工作流列表失败")


@router.get("/{workflow_id}", response_model=APIResponse[BatchWorkflow])
async def get_workflow_by_id(workflow_id: str):
    """根据ID获取工作流详情"""
    try:
        workflow = await workflow_service.get_workflow_by_id(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        return APIResponse(
            code=0,
            msg="获取工作流详情成功",
            data=workflow
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow by id {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="获取工作流详情失败")


@router.post("/", response_model=APIResponse[BatchWorkflow])
async def create_workflow(request: CreateWorkflowRequest):
    """创建新工作流"""
    try:
        workflow = await workflow_service.create_workflow(request)
        
        if not workflow:
            raise HTTPException(status_code=400, detail="创建工作流失败，可能是名称重复或指令不存在")
        
        return APIResponse(
            code=0,
            msg="工作流创建成功",
            data=workflow
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="创建工作流失败")


@router.put("/{workflow_id}", response_model=APIResponse[BatchWorkflow])
async def update_workflow(workflow_id: str, request: UpdateWorkflowRequest):
    """更新工作流"""
    try:
        workflow = await workflow_service.update_workflow(workflow_id, request)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="工作流不存在或更新失败")
        
        return APIResponse(
            code=0,
            msg="工作流更新成功",
            data=workflow
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="更新工作流失败")


@router.delete("/{workflow_id}", response_model=APIResponse[None])
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    try:
        success = await workflow_service.delete_workflow(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        return APIResponse(
            code=0,
            msg="工作流删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="删除工作流失败")


@router.post("/execute", response_model=APIResponse[ExecuteWorkflowResponse])
async def execute_workflow(request: ExecuteWorkflowRequest):
    """执行工作流"""
    try:
        result = await workflow_service.execute_workflow(request.workflow_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="工作流不存在或无法执行")
        
        return APIResponse(
            code=0,
            msg="工作流执行已启动",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {request.workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="执行工作流失败")


@router.get("/execution/{execution_id}", response_model=APIResponse[WorkflowExecutionStatus])
async def get_execution_status(execution_id: str):
    """获取工作流执行状态"""
    try:
        status = await workflow_service.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="执行记录不存在")
        
        return APIResponse(
            code=0,
            msg="获取执行状态成功",
            data=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="获取执行状态失败")


@router.post("/execution/{execution_id}/cancel", response_model=APIResponse[None])
async def cancel_execution(execution_id: str):
    """取消工作流执行"""
    try:
        success = await workflow_service.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="执行记录不存在或无法取消")
        
        return APIResponse(
            code=0,
            msg="工作流执行已取消",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="取消执行失败")