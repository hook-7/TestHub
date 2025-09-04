"""
简化的工作流API端点
"""

import logging
from typing import List
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test")
async def test_workflow():
    """
    测试工作流API
    """
    return {
        "code": 0,
        "msg": "工作流API测试成功",
        "data": {
            "status": "ok",
            "message": "工作流服务正常运行"
        }
    }


@router.get("/")
async def list_workflows_simple():
    """
    简化的工作流列表
    """
    try:
        return {
            "code": 0,
            "msg": "获取工作流列表成功",
            "data": {
                "workflows": [],
                "total": 0
            }
        }
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        return {
            "code": 500,
            "msg": f"获取工作流列表失败: {str(e)}",
            "data": None
        }


@router.post("/")
async def create_workflow_simple(workflow_data: dict):
    """
    简化的创建工作流
    """
    try:
        # 模拟创建工作流
        workflow_id = f"workflow_{len(workflow_data.get('name', ''))}"
        
        return {
            "code": 0,
            "msg": "工作流创建成功",
            "data": {
                "id": workflow_id,
                "name": workflow_data.get("name", "未命名工作流"),
                "description": workflow_data.get("description", ""),
                "steps": workflow_data.get("steps", []),
                "created_at": "2025-09-04T06:00:00Z"
            }
        }
    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        return {
            "code": 500,
            "msg": f"创建工作流失败: {str(e)}",
            "data": None
        }


@router.get("/executions")
async def list_executions_simple():
    """
    简化的工作流执行列表
    """
    try:
        # 模拟执行列表
        mock_executions = [
            {
                "id": "exec_001",
                "workflow_id": "workflow_1",
                "status": "completed",
                "current_step": None,
                "variables": {"test": "value"},
                "logs": [],
                "started_at": "2025-09-04T06:00:00Z",
                "completed_at": "2025-09-04T06:01:00Z",
                "error_message": None
            },
            {
                "id": "exec_002", 
                "workflow_id": "workflow_2",
                "status": "running",
                "current_step": "step_2",
                "variables": {"device_id": "12345"},
                "logs": [
                    {
                        "timestamp": "2025-09-04T06:00:00Z",
                        "step_id": "step_1",
                        "level": "INFO",
                        "message": "步骤开始执行"
                    }
                ],
                "started_at": "2025-09-04T06:00:30Z",
                "completed_at": None,
                "error_message": None
            }
        ]
        
        return {
            "code": 0,
            "msg": "获取执行列表成功",
            "data": {
                "executions": mock_executions,
                "total": len(mock_executions)
            }
        }
    except Exception as e:
        logger.error(f"获取执行列表失败: {e}")
        return {
            "code": 500,
            "msg": f"获取执行列表失败: {str(e)}",
            "data": None
        }


@router.get("/execution/{execution_id}")
async def get_execution_simple(execution_id: str):
    """
    简化的获取执行详情
    """
    try:
        # 模拟执行详情
        mock_execution = {
            "id": execution_id,
            "workflow_id": "workflow_1",
            "status": "completed",
            "current_step": None,
            "variables": {"device_id": "12345", "result": "success"},
            "logs": [
                {
                    "timestamp": "2025-09-04T06:00:00Z",
                    "step_id": "step_1",
                    "level": "INFO",
                    "message": "开始执行工作流"
                },
                {
                    "timestamp": "2025-09-04T06:00:30Z",
                    "step_id": "step_2", 
                    "level": "INFO",
                    "message": "步骤执行完成"
                }
            ],
            "started_at": "2025-09-04T06:00:00Z",
            "completed_at": "2025-09-04T06:01:00Z",
            "error_message": None
        }
        
        return {
            "code": 0,
            "msg": "获取执行详情成功",
            "data": mock_execution
        }
    except Exception as e:
        logger.error(f"获取执行详情失败: {e}")
        return {
            "code": 500,
            "msg": f"获取执行详情失败: {str(e)}",
            "data": None
        }