@echo off
REM backend/start_celery.bat
REM Celery Worker启动脚本 (Windows)

echo 🚀 Starting Celery Worker...

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%
set FLASK_APP=app.main.py

REM Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info --concurrency=1 --pool=solo --max-tasks-per-child=50 --logfile=celery.log --pidfile=celery.pid

pause
