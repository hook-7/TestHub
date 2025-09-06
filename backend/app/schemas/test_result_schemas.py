"""
Test Result Schemas
测试结果相关的数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class TestItemResultSchema(BaseModel):
    """测试项结果模型"""
    id: str = Field(..., description="测试项ID")
    name: str = Field(..., description="测试项名称")
    command: str = Field(..., description="执行的命令")
    expected_response: str = Field(..., description="期望响应")
    actual_response: Optional[str] = Field(None, description="实际响应")
    is_ok: bool = Field(..., description="是否通过")
    reason: str = Field(..., description="结果原因")
    timestamp: int = Field(..., description="测试时间（毫秒时间戳）")
    has_notification: bool = Field(False, description="是否有通知")
    user_choice: Optional[bool] = Field(None, description="用户选择结果")


class TestResultSchema(BaseModel):
    """测试结果模型"""
    mac_address: str = Field(..., description="MAC地址")
    test_items: List[TestItemResultSchema] = Field(..., description="测试项结果列表")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    total_tests: int = Field(..., description="总测试数")
    passed_tests: int = Field(..., description="通过测试数")
    failed_tests: int = Field(..., description="失败测试数")
    skipped_tests: int = Field(..., description="跳过测试数")
    operator: Optional[str] = Field(None, description="操作员")
    workstation: Optional[str] = Field(None, description="工位")
    device_id: Optional[str] = Field(None, description="设备ID")
    
    @field_serializer('start_time', 'end_time')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)


class SaveTestResultRequest(BaseModel):
    """保存测试结果请求模型"""
    mac_address: str = Field(..., description="MAC地址")
    test_items: List[TestItemResultSchema] = Field(..., description="测试项结果列表")
    start_time: int = Field(..., description="开始时间（毫秒时间戳）")
    end_time: Optional[int] = Field(None, description="结束时间（毫秒时间戳）")
    total_tests: int = Field(..., description="总测试数")
    passed_tests: int = Field(..., description="通过测试数")
    failed_tests: int = Field(..., description="失败测试数")
    skipped_tests: int = Field(..., description="跳过测试数")
    operator: Optional[str] = Field(None, description="操作员")
    workstation: Optional[str] = Field(None, description="工位")
    device_id: Optional[str] = Field(None, description="设备ID")


class TestResultResponse(BaseModel):
    """测试结果响应模型"""
    id: str = Field(..., description="测试结果ID")
    mac_address: str = Field(..., description="MAC地址")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    total_tests: int = Field(..., description="总测试数")
    passed_tests: int = Field(..., description="通过测试数")
    failed_tests: int = Field(..., description="失败测试数")
    skipped_tests: int = Field(..., description="跳过测试数")
    operator: Optional[str] = Field(None, description="操作员")
    workstation: Optional[str] = Field(None, description="工位")
    device_id: Optional[str] = Field(None, description="设备ID")
    created_at: datetime = Field(..., description="创建时间")
    
    @field_serializer('start_time', 'end_time', 'created_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[int]:
        """将datetime序列化为毫秒时间戳"""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)


class TestResultListResponse(BaseModel):
    """测试结果列表响应模型"""
    results: List[TestResultResponse] = Field(..., description="测试结果列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class TestResultDetailResponse(TestResultResponse):
    """测试结果详情响应模型"""
    test_items: List[TestItemResultSchema] = Field(..., description="测试项结果列表")
