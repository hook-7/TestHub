"""
Standard API Response Format
"""

from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Any = None, msg: str = "success") -> "APIResponse[Any]":
        """Create success response"""
        return cls(code=0, msg=msg, data=data)
    
    @classmethod
    def error(cls, code: int, msg: str, data: Any = None) -> "APIResponse[Any]":
        """Create error response"""
        return cls(code=code, msg=msg, data=data)
    
    @classmethod
    def param_error(cls, msg: str = "参数错误") -> "APIResponse[Any]":
        """Parameter error"""
        return cls(code=400, msg=msg)
    
    @classmethod
    def system_error(cls, msg: str = "系统错误") -> "APIResponse[Any]":
        """System error"""
        return cls(code=500, msg=msg)
    
    @classmethod
    def business_error(cls, code: int, msg: str) -> "APIResponse[Any]":
        """Business error (1xxx codes)"""
        return cls(code=1000 + code, msg=msg)