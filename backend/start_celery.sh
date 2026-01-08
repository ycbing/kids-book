#!/bin/bash
# backend/start_celery.sh
# Celery Worker启动脚本

echo "🚀 启动Celery Worker..."

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export FLASK_APP=app.main.py

# 启动Celery Worker
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=solo \
    --max-tasks-per-child=50 \
    --logfile=celery.log \
    --pidfile=celery.pid
