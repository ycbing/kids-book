# backend/app/core/celery_app.py
"""
Celery异步任务队列配置
用于处理长时间运行的任务（如绘本生成）
"""
from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 创建Celery应用实例
celery_app = Celery(
    "ai_picture_book",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery配置
celery_app.conf.update(
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # 任务配置
    task_track_started=True,  # 跟踪任务开始状态
    task_time_limit=3600,      # 任务超时时间（1小时）
    task_soft_time_limit=3300, # 软超时（55分钟）
    task_acks_late=True,       # 任务完成后才确认
    worker_prefetch_multiplier=1,  # 每次只获取一个任务

    # 结果配置
    result_expires=3600,       # 结果保留1小时
    result_extended=True,      # 允许扩展结果过期时间

    # 重试配置
    task_autoretry_for=(Exception,),  # 所有异常都自动重试
    task_retry_max_delay=300,         # 最大重试延迟5分钟
    task_retry_backoff=True,          # 启用指数退避
    task_retry_backoff_max=600,       # 最大退避时间10分钟
    task_retry_max_times=3,           # 最多重试3次

    # Worker配置
    worker_concurrency=2,       # 并发worker数量
    worker_max_tasks_per_child=50,  # 每个worker最多处理50个任务后重启

    # 路由配置（可选）
    # task_routes = {
    #     'app.tasks.book_tasks.generate_book_task': {'queue': 'book_generation'},
    #     'app.tasks.export_tasks.export_book_task': {'queue': 'export'},
    # }

    # 任务优先级
    # task_default_queue='default',
    # task_default_priority=5,
)

logger.info("✅ Celery应用初始化完成")
logger.info(f"   Broker: {settings.REDIS_URL}")
logger.info(f"   Backend: {settings.REDIS_URL}")
