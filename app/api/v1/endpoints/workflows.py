"""
Workflows API Endpoints
工作流编排API端点
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.core.response import APIResponse
from app.services.workflow_service import workflow_service
from app.schemas.workflow_schemas import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStats,
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowListResponse,
    WorkflowExecutionListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=APIResponse[WorkflowListResponse])
async def get_workflows(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取工作流列表"""
    try:
        result = await workflow_service.get_all_workflows(
            page=page,
            page_size=page_size,
            status=status,
            search=search
        )
        
        response_data = WorkflowListResponse(
            workflows=result["workflows"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
        
        return APIResponse.success(
            data=response_data,
            msg=f"获取到 {len(result['workflows'])} 个工作流"
        )
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return APIResponse.error(code=500, msg="获取工作流列表失败")


@router.get("/{workflow_id}", response_model=APIResponse[WorkflowDefinition])
async def get_workflow(workflow_id: str):
    """获取工作流详情"""
    try:
        workflow = await workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            return APIResponse.error(code=404, msg="工作流不存在")
        
        return APIResponse.success(
            data=workflow,
            msg="获取工作流成功"
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        return APIResponse.error(code=500, msg="获取工作流失败")


@router.post("/", response_model=APIResponse[WorkflowDefinition])
async def create_workflow(request: CreateWorkflowRequest):
    """创建工作流"""
    try:
        workflow = await workflow_service.create_workflow(request)
        
        return APIResponse.success(
            data=workflow,
            msg="工作流创建成功"
        )
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return APIResponse.error(code=500, msg="工作流创建失败")


@router.put("/{workflow_id}", response_model=APIResponse[WorkflowDefinition])
async def update_workflow(workflow_id: str, request: UpdateWorkflowRequest):
    """更新工作流"""
    try:
        workflow = await workflow_service.update_workflow(workflow_id, request)
        
        if not workflow:
            return APIResponse.error(code=404, msg="工作流不存在")
        
        return APIResponse.success(
            data=workflow,
            msg="工作流更新成功"
        )
        
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        return APIResponse.error(code=500, msg="工作流更新失败")


@router.delete("/{workflow_id}", response_model=APIResponse)
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    try:
        success = await workflow_service.delete_workflow(workflow_id)
        
        if not success:
            return APIResponse.error(code=404, msg="工作流不存在")
        
        return APIResponse.success(
            data=None,
            msg="工作流删除成功"
        )
        
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        return APIResponse.error(code=500, msg="工作流删除失败")


@router.post("/{workflow_id}/duplicate", response_model=APIResponse[WorkflowDefinition])
async def duplicate_workflow(workflow_id: str, request: dict):
    """复制工作流"""
    try:
        new_name = request.get("name", f"工作流副本")
        workflow = await workflow_service.duplicate_workflow(workflow_id, new_name)
        
        if not workflow:
            return APIResponse.error(code=404, msg="工作流不存在")
        
        return APIResponse.success(
            data=workflow,
            msg="工作流复制成功"
        )
        
    except Exception as e:
        logger.error(f"Error duplicating workflow {workflow_id}: {e}")
        return APIResponse.error(code=500, msg="工作流复制失败")


@router.post("/execute", response_model=APIResponse[WorkflowExecution])
async def execute_workflow(request: ExecuteWorkflowRequest):
    """执行工作流"""
    try:
        execution = await workflow_service.execute_workflow(request)
        
        return APIResponse.success(
            data=execution,
            msg="工作流执行已开始"
        )
        
    except ValueError as e:
        return APIResponse.error(code=404, msg=str(e))
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return APIResponse.error(code=500, msg="工作流执行失败")


@router.get("/executions/", response_model=APIResponse[WorkflowExecutionListResponse])
async def get_executions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    workflow_id: Optional[str] = Query(None, description="工作流ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤")
):
    """获取执行记录列表"""
    try:
        result = await workflow_service.get_executions(
            page=page,
            page_size=page_size,
            workflow_id=workflow_id,
            status=status
        )
        
        response_data = WorkflowExecutionListResponse(
            executions=result["executions"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
        
        return APIResponse.success(
            data=response_data,
            msg=f"获取到 {len(result['executions'])} 条执行记录"
        )
        
    except Exception as e:
        logger.error(f"Error getting executions: {e}")
        return APIResponse.error(code=500, msg="获取执行记录失败")


@router.get("/executions/{execution_id}", response_model=APIResponse[WorkflowExecution])
async def get_execution(execution_id: str):
    """获取执行详情"""
    try:
        execution = await workflow_service.get_execution(execution_id)
        
        if not execution:
            return APIResponse.error(code=404, msg="执行记录不存在")
        
        return APIResponse.success(
            data=execution,
            msg="获取执行记录成功"
        )
        
    except Exception as e:
        logger.error(f"Error getting execution {execution_id}: {e}")
        return APIResponse.error(code=500, msg="获取执行记录失败")


@router.post("/executions/{execution_id}/stop", response_model=APIResponse)
async def stop_execution(execution_id: str):
    """停止执行"""
    try:
        success = await workflow_service.stop_execution(execution_id)
        
        if not success:
            return APIResponse.error(code=404, msg="执行记录不存在或已停止")
        
        return APIResponse.success(
            data=None,
            msg="执行已停止"
        )
        
    except Exception as e:
        logger.error(f"Error stopping execution {execution_id}: {e}")
        return APIResponse.error(code=500, msg="停止执行失败")


@router.get("/stats", response_model=APIResponse[WorkflowStats])
async def get_stats():
    """获取工作流统计信息"""
    try:
        stats = await workflow_service.get_stats()
        
        return APIResponse.success(
            data=stats,
            msg="获取统计信息成功"
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return APIResponse.error(code=500, msg="获取统计信息失败")