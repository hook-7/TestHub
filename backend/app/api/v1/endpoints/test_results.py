"""
Test Results API Endpoints
测试结果API端点
"""

import logging
from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session
from typing import Optional
from datetime import datetime

from app.core.response import APIResponse
from app.core.database import get_session
from app.services.test_result_service import test_result_service
from app.schemas.test_result_schemas import (
    SaveTestResultRequest,
    TestResultResponse,
    TestResultDetailResponse,
    TestResultListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/save",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="保存测试结果",
    description="保存工作流测试结果到数据库",
    responses={
        201: {"description": "测试结果保存成功"},
        400: {"description": "参数错误"},
        500: {"description": "系统错误"}
    }
)
async def save_test_result(
    request: SaveTestResultRequest,
    db_session: Session = Depends(get_session)
):
    """保存测试结果"""
    try:
        result = await test_result_service.save_test_result(db_session, request)
        return APIResponse.success(data=result, msg="测试结果保存成功")
    except Exception as e:
        logger.error(f"保存测试结果失败: {e}")
        return APIResponse.error(code=500, msg=f"保存测试结果失败: {str(e)}")


@router.get(
    "/{test_result_id}",
    response_model=APIResponse,
    summary="获取测试结果详情",
    description="根据ID获取测试结果详情",
    responses={
        200: {"description": "获取成功"},
        404: {"description": "测试结果不存在"},
        500: {"description": "系统错误"}
    }
)
async def get_test_result_detail(
    test_result_id: str,
    db_session: Session = Depends(get_session)
):
    """获取测试结果详情"""
    try:
        result = await test_result_service.get_test_result_by_id(db_session, test_result_id)
        if not result:
            return APIResponse.error(code=404, msg="测试结果不存在")
        return APIResponse.success(data=result, msg="获取测试结果详情成功")
    except Exception as e:
        logger.error(f"获取测试结果详情失败: {e}")
        return APIResponse.error(code=500, msg=f"获取测试结果详情失败: {str(e)}")


@router.get(
    "/",
    response_model=APIResponse,
    summary="获取测试结果列表",
    description="获取测试结果列表，支持分页和筛选",
    responses={
        200: {"description": "获取成功"},
        500: {"description": "系统错误"}
    }
)
async def get_test_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    mac_address: Optional[str] = Query(None, description="MAC地址筛选"),
    operator: Optional[str] = Query(None, description="操作员筛选"),
    workstation: Optional[str] = Query(None, description="工位筛选"),
    device_id: Optional[str] = Query(None, description="设备ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期筛选 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期筛选 (YYYY-MM-DD)"),
    db_session: Session = Depends(get_session)
):
    """获取测试结果列表"""
    try:
        # 解析日期参数
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        
        results, total = await test_result_service.get_test_results(
            db_session,
            page=page,
            page_size=page_size,
            mac_address=mac_address,
            operator=operator,
            workstation=workstation,
            device_id=device_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        response_data = TestResultListResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return APIResponse.success(data=response_data, msg="获取测试结果列表成功")
    except ValueError as e:
        logger.error(f"日期格式错误: {e}")
        return APIResponse.error(code=400, msg="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取测试结果列表失败: {e}")
        return APIResponse.error(code=500, msg=f"获取测试结果列表失败: {str(e)}")


@router.delete(
    "/{test_result_id}",
    response_model=APIResponse,
    summary="删除测试结果",
    description="根据ID删除测试结果",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "测试结果不存在"},
        500: {"description": "系统错误"}
    }
)
async def delete_test_result(
    test_result_id: str,
    db_session: Session = Depends(get_session)
):
    """删除测试结果"""
    try:
        success = await test_result_service.delete_test_result(db_session, test_result_id)
        if not success:
            return APIResponse.error(code=404, msg="测试结果不存在")
        return APIResponse.success(msg="测试结果删除成功")
    except Exception as e:
        logger.error(f"删除测试结果失败: {e}")
        return APIResponse.error(code=500, msg=f"删除测试结果失败: {str(e)}")
