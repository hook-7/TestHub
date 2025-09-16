"""
Health Check Tests
健康检查测试
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """测试健康检查端点"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == 0
    assert data["msg"] == "系统运行正常"
    assert "status" in data["data"]
    assert "version" in data["data"]
    assert "environment" in data["data"]


def test_ping(client: TestClient):
    """测试ping端点"""
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ping"] == "pong"