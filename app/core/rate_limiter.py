"""
Rate Limiter for FastAPI
API限流器
"""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict, deque


class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """检查是否允许请求"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # 清理过期的请求记录
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        # 检查是否超过限制
        if len(client_requests) >= self.max_requests:
            return False, int(client_requests[0] + self.window_seconds - now)
        
        # 记录新请求
        client_requests.append(now)
        return True, 0


# 全局限流器实例
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def check_rate_limit(request: Request):
    """限流检查依赖项"""
    client_ip = request.client.host if request.client else "unknown"
    
    allowed, retry_after = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
            headers={"Retry-After": str(retry_after)}
        )