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