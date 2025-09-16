"""
API Versioning Support
API版本管理支持
"""

from fastapi import Header
from typing import Optional


async def get_api_version(accept_version: Optional[str] = Header(None, alias="Accept-Version")):
    """获取客户端请求的API版本"""
    return accept_version or "v1"


def validate_api_version(version: str) -> bool:
    """验证API版本是否支持"""
    supported_versions = ["v1"]
    return version in supported_versions