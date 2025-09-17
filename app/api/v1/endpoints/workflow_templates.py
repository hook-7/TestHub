"""
Workflow Template API Endpoints
工作流模板相关的API端点
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.schemas.workflow_template_schemas import (
    WorkflowTemplate, WorkflowExecution, WorkflowStats,
    CreateWorkflowTemplateRequest, UpdateWorkflowTemplateRequest,
    ExecuteWorkflowRequest, WorkflowTemplateListResponse,
    WorkflowExecutionListResponse
)
from app.services.workflow_template_service import workflow_template_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/templates", response_model=WorkflowTemplateListResponse)
async def get_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """获取工作流模板列表"""
    try:
        templates = await workflow_template_service.get_all_templates()
        
        # 应用筛选
        if category:
            templates = [t for t in templates if t.category == category]
        if status:
            templates = [t for t in templates if t.status.value == status]
        
        # 分页
        total = len(templates)
        start = (page - 1) * size
        end = start + size
        templates = templates[start:end]
        
        return WorkflowTemplateListResponse(templates=templates, total=total)
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="获取模板列表失败")


@router.get("/templates/{template_id}", response_model=WorkflowTemplate)
async def get_template(template_id: str):
    """获取工作流模板详情"""
    try:
        template = await workflow_template_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="获取模板详情失败")


@router.post("/templates", response_model=WorkflowTemplate)
async def create_template(request: CreateWorkflowTemplateRequest):
    """创建工作流模板"""
    try:
        template = await workflow_template_service.create_template(request)
        if not template:
            raise HTTPException(status_code=400, detail="创建模板失败")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="创建模板失败")


@router.put("/templates/{template_id}", response_model=WorkflowTemplate)
async def update_template(template_id: str, request: UpdateWorkflowTemplateRequest):
    """更新工作流模板"""
    try:
        template = await workflow_template_service.update_template(template_id, request)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="更新模板失败")


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """删除工作流模板"""
    try:
        success = await workflow_template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")
        return JSONResponse(content={"message": "删除成功"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="删除模板失败")


@router.post("/execute", response_model=WorkflowExecution)
async def execute_workflow(request: ExecuteWorkflowRequest):
    """执行工作流"""
    try:
        execution = await workflow_template_service.execute_workflow(request)
        if not execution:
            raise HTTPException(status_code=400, detail="执行工作流失败")
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail="执行工作流失败")


@router.get("/executions", response_model=WorkflowExecutionListResponse)
async def get_executions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_id: Optional[str] = Query(None, description="模板ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """获取工作流执行列表"""
    try:
        executions = await workflow_template_service.get_all_executions()
        
        # 应用筛选
        if template_id:
            executions = [e for e in executions if e.template_id == template_id]
        if status:
            executions = [e for e in executions if e.status == status]
        
        # 分页
        total = len(executions)
        start = (page - 1) * size
        end = start + size
        executions = executions[start:end]
        
        return WorkflowExecutionListResponse(executions=executions, total=total)
        
    except Exception as e:
        logger.error(f"Error getting executions: {e}")
        raise HTTPException(status_code=500, detail="获取执行列表失败")


@router.get("/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(execution_id: str):
    """获取工作流执行详情"""
    try:
        execution = await workflow_template_service.get_execution_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="执行实例不存在")
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="获取执行详情失败")


@router.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: str):
    """停止工作流执行"""
    try:
        success = await workflow_template_service.stop_execution(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="执行实例不存在或无法停止")
        return JSONResponse(content={"message": "停止成功"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="停止执行失败")


@router.get("/stats", response_model=WorkflowStats)
async def get_stats():
    """获取工作流统计信息"""
    try:
        stats = await workflow_template_service.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")