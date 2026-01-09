# backend/app/api/health.py
"""
健康检查API端点
用于Docker健康检查、Kubernetes liveness/readiness probes、负载均衡器健康检查
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import redis
import asyncio
from typing import Dict, Any, Optional
import logging

from app.models.database import SessionLocal, engine
from app.config import settings
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    基础健康检查（快速）
    用于确定服务是否运行

    返回简单的状态，不执行任何耗时操作
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    详细健康检查
    检查所有依赖服务的健康状态

    用于监控系统和排查问题
    包含数据库、Redis、Celery等检查
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    overall_healthy = True

    # 1. 数据库健康检查
    db_status = await check_database_health()
    health_status["checks"]["database"] = db_status
    if db_status["status"] != "healthy":
        overall_healthy = False

    # 2. Redis健康检查（如果配置了）
    if settings.REDIS_URL:
        redis_status = await check_redis_health()
        health_status["checks"]["redis"] = redis_status
        if redis_status["status"] != "healthy":
            # Redis是可选的，不影响整体健康状态
            health_status["checks"]["redis"]["optional"] = True

    # 3. Celery健康检查（如果配置了）
    if settings.REDIS_URL:
        celery_status = await check_celery_health()
        health_status["checks"]["celery"] = celery_status
        if celery_status["status"] != "healthy":
            # Celery是可选的，不影响整体健康状态
            health_status["checks"]["celery"]["optional"] = True

    # 4. API配置健康检查
    api_status = check_api_config_health()
    health_status["checks"]["api_config"] = api_status
    if api_status["status"] != "healthy":
        overall_healthy = False

    # 5. 存储健康检查
    storage_status = check_storage_health()
    health_status["checks"]["storage"] = storage_status
    if storage_status["status"] != "healthy":
        overall_healthy = False

    # 设置整体状态
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"

    # 返回相应的状态码
    return health_status


async def check_database_health() -> Dict[str, Any]:
    """
    检查数据库连接健康状态
    """
    try:
        db: Optional[Session] = None
        start_time = datetime.utcnow()

        try:
            db = SessionLocal()

            # 执行简单查询测试连接
            result = db.execute(text("SELECT 1"))
            result.fetchone()

            # 计算响应时间
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000  # 毫秒

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "database": settings.DATABASE_URL.split(":///")[0] if "://" in settings.DATABASE_URL else "unknown"
            }

        finally:
            if db:
                db.close()

    except Exception as e:
        logger.error(f"数据库健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": settings.DATABASE_URL.split(":///")[0] if "://" in settings.DATABASE_URL else "unknown"
        }


async def check_redis_health() -> Dict[str, Any]:
    """
    检查Redis连接健康状态
    """
    try:
        start_time = datetime.utcnow()

        # 创建Redis连接
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )

        # 执行PING命令
        result = redis_client.ping()

        # 关闭连接
        redis_client.close()

        # 计算响应时间
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000  # 毫秒

        if result:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "redis": settings.REDIS_URL
            }
        else:
            return {
                "status": "unhealthy",
                "error": "PING command failed",
                "redis": settings.REDIS_URL
            }

    except Exception as e:
        logger.warning(f"Redis健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "redis": settings.REDIS_URL
        }


async def check_celery_health() -> Dict[str, Any]:
    """
    检查Celery健康状态
    """
    try:
        # 尝试获取Celery统计信息
        inspect = celery_app.control.inspect()

        # 获取活跃的worker
        active_workers = inspect.active()

        if active_workers:
            return {
                "status": "healthy",
                "workers": list(active_workers.keys()),
                "celery": "Connected"
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No active Celery workers found",
                "celery": "No workers"
            }

    except Exception as e:
        logger.warning(f"Celery健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "celery": "Connection failed"
        }


def check_api_config_health() -> Dict[str, Any]:
    """
    检查API配置健康状态
    """
    checks = []
    overall_healthy = True

    # 检查文本API配置
    text_api_key, text_base_url, _ = settings.get_text_config()
    if text_api_key:
        checks.append({
            "name": "text_api",
            "status": "configured",
            "base_url": text_base_url
        })
    else:
        checks.append({
            "name": "text_api",
            "status": "missing",
            "error": "TEXT_API_KEY or OPENAI_API_KEY not configured"
        })
        overall_healthy = False

    # 检查图像API配置
    image_api_key, image_base_url, _ = settings.get_image_config()
    if image_api_key:
        checks.append({
            "name": "image_api",
            "status": "configured",
            "base_url": image_base_url
        })
    else:
        checks.append({
            "name": "image_api",
            "status": "missing",
            "error": "IMAGE_API_KEY or OPENAI_API_KEY not configured"
        })
        overall_healthy = False

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": checks
    }


def check_storage_health() -> Dict[str, Any]:
    """
    检查存储目录健康状态
    """
    import os
    from pathlib import Path

    checks = []
    overall_healthy = True

    # 检查上传目录
    upload_dir = Path(settings.UPLOAD_DIR)
    try:
        if upload_dir.exists():
            # 检查是否可写
            if os.access(upload_dir, os.W_OK):
                checks.append({
                    "name": "upload_dir",
                    "status": "accessible",
                    "path": str(upload_dir)
                })
            else:
                checks.append({
                    "name": "upload_dir",
                    "status": "not_writable",
                    "path": str(upload_dir),
                    "error": "Directory exists but not writable"
                })
                overall_healthy = False
        else:
            # 尝试创建目录
            upload_dir.mkdir(parents=True, exist_ok=True)
            checks.append({
                "name": "upload_dir",
                "status": "created",
                "path": str(upload_dir)
            })
    except Exception as e:
        checks.append({
            "name": "upload_dir",
            "status": "inaccessible",
            "path": str(upload_dir),
            "error": str(e)
        })
        overall_healthy = False

    # 检查输出目录
    output_dir = Path(settings.OUTPUT_DIR)
    try:
        if output_dir.exists():
            if os.access(output_dir, os.W_OK):
                checks.append({
                    "name": "output_dir",
                    "status": "accessible",
                    "path": str(output_dir)
                })
            else:
                checks.append({
                    "name": "output_dir",
                    "status": "not_writable",
                    "path": str(output_dir),
                    "error": "Directory exists but not writable"
                })
                overall_healthy = False
        else:
            # 尝试创建目录
            output_dir.mkdir(parents=True, exist_ok=True)
            checks.append({
                "name": "output_dir",
                "status": "created",
                "path": str(output_dir)
            })
    except Exception as e:
        checks.append({
            "name": "output_dir",
            "status": "inaccessible",
            "path": str(output_dir),
            "error": str(e)
        })
        overall_healthy = False

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": checks
    }


@router.get("/health/ready")
async def readiness_check():
    """
    就绪探针（Readiness Probe）

    检查服务是否已准备好接收请求
    与liveness不同，readiness可以表示服务正在启动或暂时无法接收请求

    Kubernetes: 使用readinessProbe确定容器是否准备好接收流量
    """
    try:
        # 检查数据库连接
        db: Optional[Session] = None
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
        finally:
            if db:
                db.close()

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/health/live")
async def liveness_check():
    """
    存活探针（Liveness Probe）

    检查服务是否存活
    如果存活探针失败，Kubernetes会重启容器

    这是快速的检查，不检查外部依赖
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
