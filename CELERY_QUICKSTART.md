# Celery任务队列 - 快速启动指南

## 📋 前提条件

### 1. 安装Redis

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Windows (使用Docker)**:
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**验证**:
```bash
redis-cli ping
# 应该返回: PONG
```

### 2. 安装Celery依赖

```bash
cd backend
pip install celery redis
```

---

## 🚀 启动步骤

### 1. 启动Celery Worker

**Linux/Mac**:
```bash
cd backend
chmod +x start_celery.sh
./start_celery.sh
```

**Windows**:
```bash
cd backend
start_celery.bat
```

**或手动启动**:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

**成功输出**:
```
✅ Celery应用初始化完成
   Broker: redis://localhost:6379/0
   Backend: redis://localhost:6379/0

 -------------- celery@xxx v5.3.4
---- **** -----
---
 * Starting...
```

### 2. 启动FastAPI服务器

**新终端窗口**:
```bash
cd backend
python -m app.main
```

### 3. 测试Celery任务

**创建绘本**:
```bash
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "测试主题",
    "keywords": ["测试"],
    "target_age": "3-6岁",
    "style": "水彩风格",
    "page_count": 2
  }'
```

**响应**:
```json
{
  "book_id": 1,
  "task_id": "xxx-xxx-xxx",
  "status": "generating",
  "message": "绘本已创建，正在生成内容..."
}
```

**查询任务状态**:
```bash
curl http://localhost:8000/api/v1/tasks/xxx-xxx-xxx
```

---

## 📊 监控Celery

### 1. 查看Worker日志

```bash
# 实时日志
tail -f backend/celery.log

# 查看最近日志
cat backend/celery.log | tail -50
```

### 2. 使用Flower（推荐）

**安装**:
```bash
pip install flower
```

**启动**:
```bash
cd backend
celery -A app.core.celery_app flower --port=5555
```

**访问**: http://localhost:5555

### 3. 命令行检查

```bash
# 查看活跃任务
celery -A app.core.celery_app inspect active

# 查看已注册任务
celery -A app.core.celery_app inspect registered

# 查看Worker统计
celery -A app.core.celery_app inspect stats
```

---

## 🛠️ 常用命令

### Worker管理

```bash
# 启动Worker
celery -A app.core.celery_app worker --loglevel=info

# 后台启动（Linux/Mac）
celery -A app.core.celery_app multi start worker --loglevel=info

# 停止Worker
celery -A app.core.celery_app multi stopwait worker

# 重启Worker
celery -A app.core.celery_app multi restart worker --loglevel=info
```

### 任务管理

```bash
# 取消任务
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/cancel

# 或使用命令行
celery -A app.core.celery_app control revoke {task_id}
```

---

## 📝 生产环境部署

### 使用Systemd（Linux）

**创建服务文件**: `/etc/systemd/system/celery.service`
```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/celery -A app.core.celery_app multi start worker --loglevel=info --logfile=/var/log/celery/worker.log
ExecStop=/usr/bin/celery -A app.core.celery_app multi stopwait worker
ExecReload=/usr/bin/celery -A app.core.celery_app multi restart worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务**:
```bash
sudo systemctl daemon-reload
sudo systemctl start celery
sudo systemctl enable celery
sudo systemctl status celery
```

### 使用Docker

**Docker Compose**:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: ./backend
    command: celery -A app.core.celery_app worker --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
```

**启动**:
```bash
docker-compose up -d
```

---

## ⚠️ 注意事项

### 1. Redis必须启动

Celery依赖Redis，必须先启动Redis：
```bash
redis-server
```

### 2. Worker必须运行

没有Worker运行时，任务会一直处于PENDING状态。

### 3. 数据库连接

任务中使用独立的数据库会话，避免连接池耗尽。

### 4. 任务参数

任务参数必须是可序列化的（JSON格式）。

---

## 🐛 调试技巧

### 1. 启用详细日志

```bash
celery -A app.core.celery_app worker --loglevel=debug
```

### 2. 查看任务执行信息

```python
# 在任务中添加日志
logger.info(f"处理绘本 {book_id}")

# 查看日志
tail -f celery.log | grep "绘本"
```

### 3. 测试任务

```python
# test_celery.py
from app.services.book_tasks import generate_book_content_task

# 同步执行（用于调试）
result = generate_book_content_task.apply_async(
    args=(1, {...}, 1),
    throw=True
)
print(result.get())
```

---

## 📚 更多信息

详细文档请查看: [TASK_QUEUE_GUIDE.md](TASK_QUEUE_GUIDE.md)
