"""
Test Configuration
测试配置文件
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_session_id():
    """模拟会话ID"""
    return "test_session_123"


@pytest.fixture
def auth_headers(mock_session_id):
    """认证请求头"""
    return {"X-Session-Id": mock_session_id}