# backend/app/core/sentry.py
"""
Sentry错误追踪模块

提供：
- 自动错误捕获
- 性能监控
- 事件上报
- 用户反馈
"""

import os
import logging
from typing import Optional, Dict, Any
from sentry_sdk import (
    init as sentry_init,
    capture_exception,
    capture_message,
    set_tag,
    set_user,
    add_breadcrumb,
    configure_scope,
)
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

logger = logging.getLogger(__name__)


class SentryConfig:
    """Sentry配置"""

    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: Optional[str] = None,
        sample_rate: float = 1.0,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
    ):
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment or os.getenv(
            "ENVIRONMENT",
            "production" if os.getenv("DEBUG") == "false" else "development"
        )
        self.sample_rate = sample_rate
        self.traces_sample_rate = traces_sample_rate
        self.profiles_sample_rate = profiles_sample_rate


def init_sentry(config: SentryConfig) -> bool:
    """
    初始化Sentry

    Args:
        config: Sentry配置

    Returns:
        bool: 是否成功初始化
    """
    if not config.dsn:
        logger.info("⚠️  Sentry DSN未配置，错误追踪未启用")
        return False

    try:
        sentry_init(
            dsn=config.dsn,
            environment=config.environment,
            # 错误采样率（1.0 = 100%）
            sample_rate=config.sample_rate,
            # 性能监控采样率（0.1 = 10%，避免过多数据）
            traces_sample_rate=config.traces_sample_rate,
            # 性能剖析采样率
            profiles_sample_rate=config.profiles_sample_rate,
            # 集成
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
            ],
            # 过滤敏感数据
            before_send=before_send_filter,
            # 忽略特定错误
            ignore_errors=[
                KeyboardInterrupt,
                SystemExit,
            ],
            # 服务器名称
            server_name=os.getenv("SERVER_NAME", "ai-picture-book"),
            # 发布版本
            release=os.getenv("APP_VERSION", "1.0.0"),
        )

        logger.info(f"✅ Sentry错误追踪已启用 (环境: {config.environment})")
        return True

    except Exception as e:
        logger.error(f"❌ Sentry初始化失败: {str(e)}")
        return False


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    过滤和修改Sentry事件

    可以用于：
    - 过滤敏感信息
    - 添加自定义标签
    - 修改事件数据
    """
    # 过滤敏感数据
    request = event.get("request", {})

    # 移除敏感请求头
    headers = request.get("headers", {})
    sensitive_headers = ["authorization", "cookie", "x-api-key"]
    for header in sensitive_headers:
        headers.pop(header, None)

    # 添加自定义标签
    if "tags" not in event:
        event["tags"] = {}

    event["tags"]["environment"] = os.getenv("ENVIRONMENT", "unknown")

    # 添加额外上下文
    if "extra" not in event:
        event["extra"] = {}

    event["extra"]["debug_mode"] = os.getenv("DEBUG", "false") == "true"

    return event


def capture_error(
    error: Exception,
    level: str = "error",
    tags: Optional[Dict[str, str]] = None,
    user: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    捕获并上报错误

    Args:
        error: 异常对象
        level: 日志级别 (error/warning/info/debug)
        tags: 自定义标签
        user: 用户信息
        extra: 额外上下文

    Returns:
        Optional[str]: 事件ID，如果Sentry未启用则返回None
    """
    if not os.getenv("SENTRY_DSN"):
        return None

    # 配置作用域
    with configure_scope() as scope:
        # 设置级别
        scope.set_level(level)

        # 添加标签
        if tags:
            for key, value in tags.items():
                set_tag(key, value)

        # 设置用户
        if user:
            set_user(user)

        # 添加额外上下文
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

    # 捕获异常
    event_id = capture_exception(error)

    if event_id:
        logger.info(f"📤 错误已上报到Sentry: {event_id}")

    return event_id


def capture_log(
    message: str,
    level: str = "info",
    tags: Optional[Dict[str, str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    捕获并上报日志消息

    Args:
        message: 日志消息
        level: 日志级别 (info/warning/error/debug)
        tags: 自定义标签
        extra: 额外上下文

    Returns:
        Optional[str]: 事件ID，如果Sentry未启用则返回None
    """
    if not os.getenv("SENTRY_DSN"):
        return None

    # 配置作用域
    with configure_scope() as scope:
        # 设置级别
        scope.set_level(level)

        # 添加标签
        if tags:
            for key, value in tags.items():
                set_tag(key, value)

        # 添加额外上下文
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

    # 捕获消息
    event_id = capture_message(message, level=level)

    if event_id:
        logger.info(f"📤 日志已上报到Sentry: {event_id}")

    return event_id


def add_breadcrumb_message(
    category: str,
    message: str,
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """
    添加面包屑（追踪用户操作路径）

    Args:
        category: 类别 (http/user/etc.)
        message: 消息
        level: 级别
        data: 额外数据
    """
    if not os.getenv("SENTRY_DSN"):
        return

    add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data or {}
    )


def set_user_context(
    user_id: Optional[str],
    email: Optional[str] = None,
    username: Optional[str] = None,
    **kwargs
):
    """
    设置用户上下文

    Args:
        user_id: 用户ID
        email: 邮箱
        username: 用户名
        **kwargs: 其他用户属性
    """
    if not os.getenv("SENTRY_DSN"):
        return

    user_data = {"id": user_id}
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    user_data.update(kwargs)

    set_user(user_data)


def set_transaction_name(name: str):
    """
    设置事务名称（用于性能监控）

    Args:
        name: 事务名称（如：GET /api/books）
    """
    if not os.getenv("SENTRY_DSN"):
        return

    from sentry_sdk import set_transaction

    set_transaction(name, op="http.server")


def set_request_context(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
):
    """
    设置请求上下文

    Args:
        method: HTTP方法
        url: 请求URL
        headers: 请求头
        params: 请求参数
    """
    if not os.getenv("SENTRY_DSN"):
        return

    add_breadcrumb(
        category="http",
        message=f"{method} {url}",
        level="info",
        data={
            "method": method,
            "url": url,
            "headers": headers or {},
            "params": params or {}
        }
    )


# ============================================
# 装饰器
# ============================================

from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


def track_errors(
    tags: Optional[Dict[str, str]] = None,
    user_context: Optional[Callable] = None,
):
    """
    错误追踪装饰器

    用法:
        @track_errors(tags={"endpoint": "create_book"})
        async def create_book(book_data: BookCreate):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # 添加面包屑
            add_breadcrumb_message(
                category="function",
                message=f"调用函数: {func.__name__}",
                level="info"
            )

            # 设置用户上下文
            if user_context:
                try:
                    user_info = user_context()
                    if user_info:
                        set_user_context(**user_info)
                except Exception:
                    pass

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                # 捕获错误
                capture_error(
                    error=e,
                    tags=tags or {},
                    extra={
                        "function": func.__name__,
                        "args": str(args)[:100],  # 限制长度
                        "kwargs": str(kwargs)[:100]
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 添加面包屑
            add_breadcrumb_message(
                category="function",
                message=f"调用函数: {func.__name__}",
                level="info"
            )

            # 设置用户上下文
            if user_context:
                try:
                    user_info = user_context()
                    if user_info:
                        set_user_context(**user_info)
                except Exception:
                    pass

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                # 捕获错误
                capture_error(
                    error=e,
                    tags=tags or {},
                    extra={
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    }
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_performance(
    transaction_name: Optional[str] = None,
):
    """
    性能追踪装饰器

    用法:
        @track_performance("create_book")
        async def create_book(book_data: BookCreate):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            import time
            start_time = time.time()

            # 设置事务名称
            name = transaction_name or func.__name__
            set_transaction_name(name)

            try:
                result = await func(*args, **kwargs)
                return result

            finally:
                duration = time.time() - start_time
                add_breadcrumb_message(
                    category="performance",
                    message=f"{name} 完成 (耗时: {duration:.2f}s)",
                    level="info"
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            import time
            start_time = time.time()

            # 设置事务名称
            name = transaction_name or func.__name__
            set_transaction_name(name)

            try:
                result = func(*args, **kwargs)
                return result

            finally:
                duration = time.time() - start_time
                add_breadcrumb_message(
                    category="performance",
                    message=f"{name} 完成 (耗时: {duration:.2f}s)",
                    level="info"
                )

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
