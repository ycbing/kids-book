# backend/app/core/rate_limit.py
"""
API限流中间件
"""

import time
import logging
from typing import Optional
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """限流器"""

    def __init__(self):
        self.storage = {}

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求（滑动窗口）"""
        current_time = time.time()
        requests = self.storage.get(key, [])
        
        # 移除窗口外的请求
        requests = [t for t in requests if current_time - t < window]
        
        if len(requests) >= limit:
            return False
        
        requests.append(current_time)
        self.storage[key] = requests
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        client_id = request.client.host if request.client else "unknown"
        
        if not self.rate_limiter.is_allowed(client_id, self.requests_per_minute, 60):
            return Response(
                content='{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"请求过于频繁"}}',
                status_code=429,
                media_type="application/json"
            )

        return await call_next(request)
