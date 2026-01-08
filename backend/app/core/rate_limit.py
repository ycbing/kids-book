# backend/app/core/rate_limit.py
"""
API限流模块
使用Redis实现API请求频率限制，防止滥用和DDoS攻击
"""
from functools import wraps
from typing import Optional, Callable
import time
import logging

from fastapi import Request, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis未安装，限流功能将使用内存模式（不支持分布式）")


class RateLimiter:
    """限流器基类"""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit"
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        检查是否允许请求

        返回: (是否允许, 限制信息)
        """
        raise NotImplementedError


class RedisRateLimiter(RateLimiter):
    """基于Redis的分布式限流器"""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit",
        redis_url: Optional[str] = None
    ):
        super().__init__(max_requests, window_seconds, key_prefix)
        self.redis_url = redis_url or settings.REDIS_URL
        self._client = None

    @property
    def client(self):
        """懒加载Redis客户端"""
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                # 测试连接
                self._client.ping()
                logger.info(f"✅ Redis限流器连接成功: {self.redis_url}")
            except Exception as e:
                logger.error(f"❌ Redis连接失败: {e}，将降级到内存限流")
                self._client = None
        return self._client

    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """使用Redis滑动窗口算法检查限流"""
        if not self.client:
            # 降级到内存限流
            return MemoryRateLimiter(
                self.max_requests,
                self.window_seconds,
                self.key_prefix
            ).is_allowed(identifier)

        key = f"{self.key_prefix}:{identifier}"
        current_time = time.time()

        try:
            pipe = self.client.pipeline()

            # 移除窗口外的记录
            pipe.zremrangebyscore(key, 0, current_time - self.window_seconds)

            # 获取当前请求数
            pipe.zcard(key)

            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})

            # 设置过期时间
            pipe.expire(key, self.window_seconds + 1)

            results = pipe.execute()
            current_count = results[1]

            allowed = current_count < self.max_requests

            return allowed, {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_count),
                "reset": int(current_time + self.window_seconds)
            }

        except Exception as e:
            logger.error(f"Redis限流检查失败: {e}")
            # 出错时允许请求通过（降级策略）
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset": int(time.time() + self.window_seconds)
            }


class MemoryRateLimiter(RateLimiter):
    """基于内存的限流器（单机，不支持分布式）"""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit"
    ):
        super().__init__(max_requests, window_seconds, key_prefix)
        self._requests: dict = {}  # {identifier: [timestamp1, timestamp2, ...]}
        self._last_cleanup: float = time.time()

    def _cleanup_old_requests(self):
        """清理过期的请求记录"""
        current_time = time.time()

        # 每60秒清理一次
        if current_time - self._last_cleanup < 60:
            return

        cutoff_time = current_time - self.window_seconds

        for identifier in list(self._requests.keys()):
            # 过滤掉窗口外的请求
            self._requests[identifier] = [
                ts for ts in self._requests[identifier]
                if ts > cutoff_time
            ]

            # 删除空记录
            if not self._requests[identifier]:
                del self._requests[identifier]

        self._last_cleanup = current_time

    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """检查内存中的请求计数"""
        current_time = time.time()

        # 定期清理
        self._cleanup_old_requests()

        # 获取或初始化该标识符的请求记录
        if identifier not in self._requests:
            self._requests[identifier] = []

        # 过滤掉窗口外的请求
        cutoff_time = current_time - self.window_seconds
        self._requests[identifier] = [
            ts for ts in self._requests[identifier]
            if ts > cutoff_time
        ]

        current_count = len(self._requests[identifier])

        # 添加当前请求
        self._requests[identifier].append(current_time)

        allowed = current_count < self.max_requests

        return allowed, {
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count - 1),
            "reset": int(current_time + self.window_seconds)
        }


def get_rate_limiter(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_prefix: str = "rate_limit"
) -> RateLimiter:
    """
    获取限流器实例

    优先使用Redis限流器，如果Redis不可用则使用内存限流器
    """
    if REDIS_AVAILABLE:
        try:
            return RedisRateLimiter(max_requests, window_seconds, key_prefix)
        except Exception:
            logger.warning("Redis限流器初始化失败，使用内存限流器")

    return MemoryRateLimiter(max_requests, window_seconds, key_prefix)


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    API限流装饰器

    参数:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        key_func: 自定义标识符函数，接收Request返回str
                  默认使用IP地址或user_id

    使用示例:
        @router.get("/books")
        @rate_limit(max_requests=10, window_seconds=60)
        async def list_books():
            ...
    """
    limiter = get_rate_limiter(max_requests, window_seconds, "api_limit")

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取Request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                # 如果没有Request对象，直接调用函数
                return await func(*args, **kwargs)

            # 获取限流标识符
            if key_func:
                identifier = key_func(request)
            else:
                # 优先使用user_id，其次是IP
                user_id = getattr(request.state, "user_id", None)
                identifier = str(user_id) if user_id else request.client.host

            # 检查限流
            allowed, info = limiter.is_allowed(identifier)

            # 添加限流信息到响应头
            request.state.rate_limit_info = info

            if not allowed:
                logger.warning(
                    f"⚠️  限流触发: {identifier} "
                    f"({max_requests}次/{window_seconds}秒)"
                )

                from app.core.exceptions import RateLimitException
                raise RateLimitException(
                    f"请求过于频繁，请稍后再试。"
                    f"限制：{max_requests}次/{window_seconds}秒"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


class RateLimitMiddleware:
    """限流中间件 - 对所有请求应用限流"""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: Optional[list] = None
    ):
        self.limiter = get_rate_limiter(max_requests, window_seconds, "middleware")
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def __call__(self, request: Request, call_next):
        """处理请求"""
        # 跳过排除的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 获取标识符
        user_id = getattr(request.state, "user_id", None)
        identifier = str(user_id) if user_id else request.client.host

        # 检查限流
        allowed, info = self.limiter.is_allowed(identifier)

        # 存储限流信息到request state
        request.state.rate_limit_info = info

        if not allowed:
            from fastapi.responses import JSONResponse
            logger.warning(f"⚠️  全局限流触发: {identifier}")

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"请求过于频繁，请稍后再试",
                        "details": {
                            "limit": info["limit"],
                            "window": self.limiter.window_seconds
                        }
                    },
                    "path": request.url.path
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(self.limiter.window_seconds)
                }
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response


# 预定义的限流配置
RATE_LIMIT_CONFIGS = {
    "strict": (10, 60),      # 严格：10次/分钟
    "moderate": (60, 60),    # 适中：60次/分钟
    "loose": (200, 60),      # 宽松：200次/分钟
    "hourly": (1000, 3600),  # 每小时：1000次/小时
}
