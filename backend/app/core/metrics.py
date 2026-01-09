# backend/app/core/metrics.py
"""
Prometheus性能监控模块

提供：
- HTTP请求指标
- 业务指标
- 系统资源指标
"""

import time
import logging
from typing import Callable, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import CollectorRegistry, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ============================================
# HTTP指标
# ============================================

http_requests_total = Counter(
    "http_requests_total",
    "HTTP请求总数",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP请求延迟",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "当前正在处理的HTTP请求数",
    ["method", "endpoint"]
)

# ============================================
# 业务指标
# ============================================

# 绘本创建
books_created_total = Counter(
    "books_created_total",
    "创建的绘本总数",
    ["status"]
)

books_creation_duration_seconds = Histogram(
    "books_creation_duration_seconds",
    "绘本创建耗时"
)

books_in_progress = Gauge(
    "books_in_progress",
    "当前正在创建的绘本数量"
)

# AI服务调用
ai_api_calls_total = Counter(
    "ai_api_calls_total",
    "AI API调用总数",
    ["service", "model", "status"]
)

ai_api_duration_seconds = Histogram(
    "ai_api_duration_seconds",
    "AI API调用耗时",
    ["service", "model"]
)

# 数据库操作
db_queries_total = Counter(
    "db_queries_total",
    "数据库查询总数",
    ["operation", "table"]
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "数据库查询耗时",
    ["operation", "table"]
)

db_connections_in_use = Gauge(
    "db_connections_in_use",
    "当前使用的数据库连接数"
)

# ============================================
# 系统资源指标
# ============================================

system_info = Info(
    "system",
    "系统信息"
)

active_users_total = Gauge(
    "active_users_total",
    "当前活跃用户数"
)

cache_hits_total = Counter(
    "cache_hits_total",
    "缓存命中次数",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "缓存未命中次数",
    ["cache_type"]
)

# ============================================
# 自定义装饰器
# ============================================

def track_time(histogram: Histogram, *label_values):
    """
    跟踪函数执行时间的装饰器

    用法:
        @track_time(http_request_duration_seconds, "GET", "/api/books")
        async def get_books():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.labels(*label_values).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.labels(*label_values).observe(duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_counter(counter: Counter, *label_values):
    """
    跟踪事件计数的装饰器

    用法:
        @track_counter(books_created_total, "success")
        async def create_book():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                counter.labels(*label_values).inc()
                return result
            except Exception as e:
                counter.labels(*label_values, "error").inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                counter.labels(*label_values).inc()
                return result
            except Exception as e:
                counter.labels(*label_values, "error").inc()
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================
# Prometheus中间件
# ============================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus监控中间件

    自动收集HTTP请求指标：
    - 请求总数
    - 请求延迟
    - 并发请求数
    """

    async def dispatch(self, request: Request, call_next):
        # 获取请求方法
        method = request.method

        # 获取端点路径
        endpoint = request.url.path
        # 替换路径参数为占位符
        for part in endpoint.split("/"):
            if part.isdigit():
                endpoint = endpoint.replace(part, "{id}")

        # 增加并发计数
        http_requests_in_progress.labels(method, endpoint).inc()

        # 记录开始时间
        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 记录指标
            status = response.status_code
            http_requests_total.labels(method, endpoint, status).inc()

            # 记录延迟
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method, endpoint).observe(duration)

            return response

        except Exception as e:
            # 记录错误
            http_requests_total.labels(method, endpoint, 500).inc()

            # 记录延迟
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method, endpoint).observe(duration)

            raise

        finally:
            # 减少并发计数
            http_requests_in_progress.labels(method, endpoint).dec()


# ============================================
# 指标暴露端点
# ============================================

from fastapi import Response
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def setup_metrics(app: FastAPI):
    """
    设置Prometheus监控

    用法:
        from app.core.metrics import setup_metrics

        app = FastAPI()
        setup_metrics(app)
    """

    # 添加Prometheus中间件
    app.add_middleware(PrometheusMiddleware)

    # 添加metrics端点
    @app.get("/metrics")
    async def metrics():
        """
        Prometheus指标暴露端点

        Prometheus会定期抓取这个端点获取指标数据
        """
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    # 设置系统信息
    system_info.info({
        "version": "1.0.0",
        "name": "AI绘本创作平台"
    })

    logger.info("✅ Prometheus监控已启用")


# ============================================
# 业务指标辅助函数
# ============================================

async def track_book_creation(status: str, duration: float):
    """
    跟踪绘本创建指标

    Args:
        status: 创建状态 (success/error)
        duration: 创建耗时（秒）
    """
    books_created_total.labels(status).inc()
    books_creation_duration_seconds.observe(duration)


async def track_ai_api_call(service: str, model: str, status: str, duration: float):
    """
    跟踪AI API调用指标

    Args:
        service: 服务名称 (text/image)
        model: 模型名称
        status: 调用状态
        duration: 调用耗时（秒）
    """
    ai_api_calls_total.labels(service, model, status).inc()
    ai_api_duration_seconds.labels(service, model).observe(duration)


async def track_db_query(operation: str, table: str, duration: float):
    """
    跟踪数据库查询指标

    Args:
        operation: 操作类型 (select/update/delete/insert)
        table: 表名
        duration: 查询耗时（秒）
    """
    db_queries_total.labels(operation, table).inc()
    db_query_duration_seconds.labels(operation, table).observe(duration)


def update_active_users(count: int):
    """
    更新活跃用户数

    Args:
        count: 活跃用户数量
    """
    active_users_total.set(count)


def update_db_connections(count: int):
    """
    更新数据库连接数

    Args:
        count: 连接数
    """
    db_connections_in_use.set(count)


def track_cache_hit(cache_type: str):
    """
    跟踪缓存命中

    Args:
        cache_type: 缓存类型 (redis/memory)
    """
    cache_hits_total.labels(cache_type).inc()


def track_cache_miss(cache_type: str):
    """
    跟踪缓存未命中

    Args:
        cache_type: 缓存类型 (redis/memory)
    """
    cache_misses_total.labels(cache_type).inc()


def update_books_in_progress(count: int):
    """
    更新正在创建的绘本数量

    Args:
        count: 数量
    """
    books_in_progress.set(count)
