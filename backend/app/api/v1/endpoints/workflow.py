"""
工作流自动化API路由
"""
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import Optional, List
import logging
import json

from app.schemas.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionRequest,
    UserConfirmationRequest,
    WebSocketMessage,
    WorkflowStatus
)
from app.services.workflow_engine import workflow_engine
from app.core.response import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["工作流自动化"])


@router.get("/workflows", response_model=dict)
async def get_workflows():
    """获取工作流列表"""
    try:
        workflows = workflow_engine.get_workflows()
        workflows_data = [wf.model_dump() for wf in workflows]
        return APIResponse.success(data=workflows_data)
    except Exception as e:
        logger.error(f"API: 获取工作流列表失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取工作流列表失败: {e}")


@router.get("/workflows/{workflow_id}", response_model=dict)
async def get_workflow(workflow_id: str):
    """获取工作流定义"""
    try:
        workflow = workflow_engine.get_workflow(workflow_id)
        if not workflow:
            return APIResponse.error(code=404, msg="工作流不存在")
        
        return APIResponse.success(data=workflow.model_dump())
    except Exception as e:
        logger.error(f"API: 获取工作流失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取工作流失败: {e}")


@router.post("/workflows/{workflow_id}/execute", response_model=dict)
async def execute_workflow(workflow_id: str, request: WorkflowExecutionRequest):
    """执行工作流"""
    try:
        if request.workflow_id != workflow_id:
            return APIResponse.error(code=400, msg="工作流ID不匹配")
        
        execution = await workflow_engine.start_workflow(
            workflow_id=workflow_id,
            input_variables=request.input_variables,
            operator_id=request.operator_id,
            workstation_id=request.workstation_id
        )
        
        logger.info(f"API: 工作流执行已启动 - {execution.execution_id}")
        return APIResponse.success(data=execution.model_dump())
    
    except ValueError as e:
        logger.warning(f"API: 工作流执行失败 - {e}")
        return APIResponse.error(code=400, msg=str(e))
    except Exception as e:
        logger.error(f"API: 工作流执行异常 - {e}")
        return APIResponse.error(code=500, msg=f"执行工作流失败: {e}")


@router.get("/executions/{execution_id}", response_model=dict)
async def get_execution(execution_id: str):
    """获取执行实例"""
    try:
        execution = workflow_engine.get_execution(execution_id)
        if not execution:
            return APIResponse.error(code=404, msg="执行实例不存在")
        
        return APIResponse.success(data=execution.model_dump())
    except Exception as e:
        logger.error(f"API: 获取执行实例失败 - {e}")
        return APIResponse.error(code=500, msg=f"获取执行实例失败: {e}")


@router.post("/executions/{execution_id}/confirm", response_model=dict)
async def confirm_workflow_step(execution_id: str, confirmation: UserConfirmationRequest):
    """确认工作流步骤"""
    try:
        if confirmation.execution_id != execution_id:
            return APIResponse.error(code=400, msg="执行ID不匹配")
        
        await workflow_engine.handle_user_confirmation(confirmation)
        
        logger.info(f"API: 工作流步骤确认成功 - {execution_id}/{confirmation.step_id}")
        return APIResponse.success(data={"message": "确认成功"})
    
    except Exception as e:
        logger.error(f"API: 工作流步骤确认失败 - {e}")
        return APIResponse.error(code=500, msg=f"确认失败: {e}")


@router.post("/executions/{execution_id}/pause", response_model=dict)
async def pause_workflow(execution_id: str):
    """暂停工作流"""
    try:
        await workflow_engine.pause_workflow(execution_id)
        return APIResponse.success(data={"message": "工作流已暂停"})
    except Exception as e:
        logger.error(f"API: 暂停工作流失败 - {e}")
        return APIResponse.error(code=500, msg=f"暂停工作流失败: {e}")


@router.post("/executions/{execution_id}/resume", response_model=dict)
async def resume_workflow(execution_id: str):
    """恢复工作流"""
    try:
        await workflow_engine.resume_workflow(execution_id)
        return APIResponse.success(data={"message": "工作流已恢复"})
    except Exception as e:
        logger.error(f"API: 恢复工作流失败 - {e}")
        return APIResponse.error(code=500, msg=f"恢复工作流失败: {e}")


@router.post("/executions/{execution_id}/cancel", response_model=dict)
async def cancel_workflow(execution_id: str):
    """取消工作流"""
    try:
        await workflow_engine.cancel_workflow(execution_id)
        return APIResponse.success(data={"message": "工作流已取消"})
    except Exception as e:
        logger.error(f"API: 取消工作流失败 - {e}")
        return APIResponse.error(code=500, msg=f"取消工作流失败: {e}")


# WebSocket连接管理
class WorkflowWebSocketManager:
    """工作流WebSocket管理器"""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workstation_id: str):
        """连接WebSocket"""
        await websocket.accept()
        
        if workstation_id not in self.connections:
            self.connections[workstation_id] = []
        
        self.connections[workstation_id].append(websocket)
        logger.info(f"WebSocket连接已建立: 工位 {workstation_id}")
    
    async def disconnect(self, websocket: WebSocket, workstation_id: str):
        """断开WebSocket连接"""
        if workstation_id in self.connections:
            if websocket in self.connections[workstation_id]:
                self.connections[workstation_id].remove(websocket)
            
            if not self.connections[workstation_id]:
                del self.connections[workstation_id]
        
        logger.info(f"WebSocket连接已断开: 工位 {workstation_id}")
    
    async def broadcast_to_workstation(self, workstation_id: str, message: dict):
        """向指定工位广播消息"""
        if workstation_id not in self.connections:
            logger.warning(f"工位 {workstation_id} 没有WebSocket连接")
            return
        
        disconnected = []
        for websocket in self.connections[workstation_id]:
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"WebSocket发送失败: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect(ws, workstation_id)


# WebSocket管理器实例
ws_manager = WorkflowWebSocketManager()

# 将WebSocket管理器注入到工作流引擎
workflow_engine.websocket_manager = ws_manager


@router.websocket("/ws/{workstation_id}")
async def workflow_websocket(websocket: WebSocket, workstation_id: str):
    """工作流WebSocket连接"""
    await ws_manager.connect(websocket, workstation_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            if message.get("type") == "user_confirmation":
                confirmation = UserConfirmationRequest(**message["data"])
                await workflow_engine.handle_user_confirmation(confirmation)
            elif message.get("type") == "heartbeat":
                # 心跳消息
                await websocket.send_text(json.dumps({"type": "pong"}))
            
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, workstation_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        await ws_manager.disconnect(websocket, workstation_id)