"""
Common Schemas
通用数据模型
"""

from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """API统一响应格式"""
    code: int = Field(..., description="响应码，0表示成功")
    msg: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    model_config = {
        "json_encoders": {
            # 如果需要特殊编码可以在这里添加
        }
    }