"""
Test Result Service
测试结果服务层
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlmodel import Session, select, func, desc

from app.core.database import TestResult, TestItemResult
from app.schemas.test_result_schemas import (
    SaveTestResultRequest, 
    TestResultResponse, 
    TestItemResultSchema,
    TestResultDetailResponse
)

logger = logging.getLogger(__name__)


class TestResultService:
    """测试结果服务类"""

    def __init__(self):
        self.logger = logger

    async def save_test_result(
        self, 
        session: Session, 
        request: SaveTestResultRequest
    ) -> TestResultResponse:
        """保存测试结果"""
        try:
            # 生成测试结果ID
            test_result_id = str(uuid.uuid4())
            
            # 创建测试结果主记录
            test_result = TestResult(
                id=test_result_id,
                mac_address=request.mac_address,
                start_time=datetime.fromtimestamp(request.start_time / 1000),
                end_time=datetime.fromtimestamp(request.end_time / 1000) if request.end_time else None,
                total_tests=request.total_tests,
                passed_tests=request.passed_tests,
                failed_tests=request.failed_tests,
                skipped_tests=request.skipped_tests,
                operator=request.operator,
                workstation=request.workstation,
                device_id=request.device_id
            )
            
            session.add(test_result)
            session.commit()
            session.refresh(test_result)
            
            # 创建测试项结果记录
            test_items = []
            for item in request.test_items:
                item_id = str(uuid.uuid4())
                test_item = TestItemResult(
                    id=item_id,
                    test_result_id=test_result_id,
                    command_id=item.id,
                    name=item.name,
                    command=item.command,
                    expected_response=item.expected_response,
                    actual_response=item.actual_response,
                    is_ok=item.is_ok,
                    reason=item.reason,
                    timestamp=datetime.fromtimestamp(item.timestamp / 1000),
                    has_notification=item.has_notification,
                    user_choice=item.user_choice
                )
                test_items.append(test_item)
                session.add(test_item)
            
            session.commit()
            
            # 返回响应
            return TestResultResponse(
                id=test_result.id,
                mac_address=test_result.mac_address,
                start_time=test_result.start_time,
                end_time=test_result.end_time,
                total_tests=test_result.total_tests,
                passed_tests=test_result.passed_tests,
                failed_tests=test_result.failed_tests,
                skipped_tests=test_result.skipped_tests,
                operator=test_result.operator,
                workstation=test_result.workstation,
                device_id=test_result.device_id,
                created_at=test_result.created_at
            )
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"保存测试结果失败: {e}")
            raise

    async def get_test_result_by_id(
        self, 
        session: Session, 
        test_result_id: str
    ) -> Optional[TestResultDetailResponse]:
        """根据ID获取测试结果详情"""
        try:
            # 获取测试结果主记录
            statement = select(TestResult).where(TestResult.id == test_result_id)
            test_result = session.exec(statement).first()
            
            if not test_result:
                return None
            
            # 获取测试项结果
            statement = select(TestItemResult).where(TestItemResult.test_result_id == test_result_id)
            test_items = session.exec(statement).all()
            
            # 转换为schema格式
            test_item_schemas = [
                TestItemResultSchema(
                    id=item.command_id,
                    name=item.name,
                    command=item.command,
                    expected_response=item.expected_response,
                    actual_response=item.actual_response,
                    is_ok=item.is_ok,
                    reason=item.reason,
                    timestamp=item.timestamp,
                    has_notification=item.has_notification,
                    user_choice=item.user_choice
                )
                for item in test_items
            ]
            
            return TestResultDetailResponse(
                id=test_result.id,
                mac_address=test_result.mac_address,
                start_time=test_result.start_time,
                end_time=test_result.end_time,
                total_tests=test_result.total_tests,
                passed_tests=test_result.passed_tests,
                failed_tests=test_result.failed_tests,
                skipped_tests=test_result.skipped_tests,
                operator=test_result.operator,
                workstation=test_result.workstation,
                device_id=test_result.device_id,
                created_at=test_result.created_at,
                test_items=test_item_schemas
            )
            
        except Exception as e:
            self.logger.error(f"获取测试结果失败: {e}")
            raise

    async def get_test_results(
        self, 
        session: Session,
        page: int = 1,
        page_size: int = 20,
        mac_address: Optional[str] = None,
        operator: Optional[str] = None,
        workstation: Optional[str] = None,
        device_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[TestResultResponse], int]:
        """获取测试结果列表"""
        try:
            # 构建查询条件
            statement = select(TestResult)
            
            if mac_address:
                statement = statement.where(TestResult.mac_address == mac_address)
            if operator:
                statement = statement.where(TestResult.operator == operator)
            if workstation:
                statement = statement.where(TestResult.workstation == workstation)
            if device_id:
                statement = statement.where(TestResult.device_id == device_id)
            if start_date:
                statement = statement.where(TestResult.created_at >= start_date)
            if end_date:
                statement = statement.where(TestResult.created_at <= end_date)
            
            # 获取总数
            count_statement = select(func.count()).select_from(statement.subquery())
            total = session.exec(count_statement).first()
            
            # 分页和排序
            statement = statement.order_by(desc(TestResult.created_at))
            statement = statement.offset((page - 1) * page_size).limit(page_size)
            
            results = session.exec(statement).all()
            
            # 转换为响应格式
            test_results = [
                TestResultResponse(
                    id=result.id,
                    mac_address=result.mac_address,
                    start_time=result.start_time,
                    end_time=result.end_time,
                    total_tests=result.total_tests,
                    passed_tests=result.passed_tests,
                    failed_tests=result.failed_tests,
                    skipped_tests=result.skipped_tests,
                    operator=result.operator,
                    workstation=result.workstation,
                    device_id=result.device_id,
                    created_at=result.created_at
                )
                for result in results
            ]
            
            return test_results, total
            
        except Exception as e:
            self.logger.error(f"获取测试结果列表失败: {e}")
            raise

    async def delete_test_result(
        self, 
        session: Session, 
        test_result_id: str
    ) -> bool:
        """删除测试结果"""
        try:
            # 先删除测试项结果
            statement = select(TestItemResult).where(TestItemResult.test_result_id == test_result_id)
            test_items = session.exec(statement).all()
            for item in test_items:
                session.delete(item)
            
            # 删除测试结果主记录
            statement = select(TestResult).where(TestResult.id == test_result_id)
            test_result = session.exec(statement).first()
            if test_result:
                session.delete(test_result)
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"删除测试结果失败: {e}")
            raise


# 创建服务实例
test_result_service = TestResultService()
