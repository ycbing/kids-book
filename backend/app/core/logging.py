# backend/app/core/logging.py
"""
结构化日志系统
提供JSON格式化日志和日志轮转功能
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from app.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON格式化器
    将日志记录格式化为JSON结构，便于日志分析和监控
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON

        字段说明:
        - timestamp: ISO 8601格式的时间戳
        - level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        - logger: 日志记录器名称
        - message: 日志消息
        - module: 模块名称
        - function: 函数名称
        - line: 行号
        - process: 进程ID
        - thread: 线程ID
        - extra: 额外的自定义字段
        - exception: 异常信息（如果有）
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }

        # 添加额外字段（通过logging.xxx(extra={})传入）
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # 添加其他自定义字段
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'exc_info', 'exc_text', 'stack_info',
                'getMessage', 'message'
            }:
                if not key.startswith('_'):
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器（开发环境使用）
    为不同级别的日志添加颜色，提升可读性
    """

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # 格式化消息
        result = super().format(record)

        # 恢复原始levelname（避免影响其他handler）
        record.levelname = levelname

        return result


def setup_logging():
    """
    配置应用日志系统

    功能:
    - 控制台输出（开发环境彩色，生产环境JSON）
    - 文件输出（日志轮转）
    - 不同日志级别
    - 错误日志单独记录
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # 清除现有的handlers
    logger.handlers.clear()

    # ========== 控制台处理器 ==========
    if settings.DEBUG:
        # 开发环境：彩色文本格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    else:
        # 生产环境：JSON格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = JSONFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # ========== 文件处理器（仅生产环境） ==========
    if not settings.DEBUG:
        # 应用日志（所有级别）
        app_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,               # 保留10个备份
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_formatter = JSONFormatter()
        app_handler.setFormatter(app_formatter)
        logger.addHandler(app_handler)

        # 错误日志（ERROR及以上）
        error_handler = RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,               # 保留10个备份
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = JSONFormatter()
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

        # 访问日志（按天轮转）
        access_handler = TimedRotatingFileHandler(
            log_dir / "access.log",
            when='midnight',             # 每天午夜轮转
            interval=1,                  # 每天1个文件
            backupCount=30,              # 保留30天
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.suffix = "%Y-%m-%d"  # 文件名后缀
        access_formatter = JSONFormatter()
        access_handler.setFormatter(access_formatter)

        # 创建专门的访问日志记录器
        access_logger = logging.getLogger("access")
        access_logger.setLevel(logging.INFO)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False  # 不传播到根logger

    # 配置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    使用示例:
        logger = get_logger(__name__)
        logger.info("处理请求", extra={"user_id": 123, "request_id": "abc"})
    """
    return logging.getLogger(name)


class RequestLogger:
    """
    请求日志记录器
    用于记录HTTP请求的详细信息
    """

    def __init__(self):
        self.logger = logging.getLogger("access")

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        client_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """
        记录HTTP请求

        参数:
            method: HTTP方法
            path: 请求路径
            status_code: 响应状态码
            duration: 请求处理时长（秒）
            client_ip: 客户端IP
            user_id: 用户ID
            request_id: 请求ID
            **kwargs: 其他自定义字段
        """
        log_data = {
            "type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": client_ip,
            "user_id": user_id,
            "request_id": request_id,
            **kwargs
        }

        # 根据状态码选择日志级别
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        self.logger.log(level, json.dumps(log_data, ensure_ascii=False))


class ErrorLogger:
    """
    错误日志记录器
    用于记录应用错误和异常
    """

    def __init__(self):
        self.logger = logging.getLogger("app")

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: int = logging.ERROR
    ):
        """
        记录错误

        参数:
            error: 异常对象
            context: 上下文信息
            level: 日志级别
        """
        log_data = {
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        self.logger.log(
            level,
            json.dumps(log_data, ensure_ascii=False),
            exc_info=error if level == logging.ERROR else None
        )

    def log_api_error(
        self,
        error_code: str,
        message: str,
        path: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录API错误

        参数:
            error_code: 错误码
            message: 错误消息
            path: 请求路径
            status_code: HTTP状态码
            details: 错误详情
        """
        log_data = {
            "type": "api_error",
            "error_code": error_code,
            "message": message,
            "path": path,
            "status_code": status_code,
            "details": details or {}
        }

        self.logger.error(json.dumps(log_data, ensure_ascii=False))


# 创建全局实例
request_logger = RequestLogger()
error_logger = ErrorLogger()


def log_with_context(logger: logging.Logger, message: str, **context):
    """
    带上下文的日志记录

    使用示例:
        log_with_context(logger, "用户登录", user_id=123, ip="192.168.1.1")
    """
    extra = {"context": context} if context else {}
    logger.info(message, extra=extra)
