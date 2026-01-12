# 生产环境部署指南

## 目录

- [环境要求](#环境要求)
- [部署前准备](#部署前准备)
- [快速部署](#快速部署)
- [详细配置](#详细配置)
- [反向代理配置](#反向代理配置)
- [监控和维护](#监控和维护)
- [备份和恢复](#备份和恢复)
- [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 10GB | 50GB+ SSD |
| 网络 | 10Mbps | 100Mbps+ |

### 软件要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) 推荐
- **Nginx**: 1.18+ (用于反向代理)

---

## 部署前准备

### 1. 克隆代码

```bash
# 克隆仓库
git clone https://github.com/your-org/ai-picture-book.git
cd ai-picture-book

# 切换到生产分支
git checkout main
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

**必须配置的变量**:

```bash
# ===== 应用配置 =====
APP_NAME=AI绘本创作平台
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production

# ===== 数据库配置 =====
# 开发环境使用SQLite
DATABASE_URL=sqlite:///./data/picturebook.db

# 生产环境推荐PostgreSQL
# DATABASE_URL=postgresql://user:password@postgres:5432/picturebook

# ===== Redis配置（推荐用于生产）=====
REDIS_URL=redis://redis:6379/0

# ===== AI服务配置 =====
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
STABILITY_API_KEY=your-stability-api-key

# ===== CORS配置 =====
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ===== 文件存储 =====
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs
MAX_UPLOAD_SIZE=10485760

# ===== 监控配置 =====
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_METRICS=true
```

### 3. 创建必要的目录

```bash
# 创建数据和上传目录
mkdir -p data uploads outputs logs

# 设置目录权限
chmod 755 data uploads outputs logs
```

---

## 快速部署

### 使用Docker Compose（推荐）

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 检查健康状态
curl http://localhost:8000/health
```

**服务列表**:

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | FastAPI后端 |
| frontend | 3000 | React前端（开发） |
| postgres | 5432 | PostgreSQL数据库 |
| redis | 6379 | Redis缓存 |
| celery | - | 异步任务队列 |
| flower | 5555 | Celery监控 |

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 详细配置

### 生产环境Docker Compose

**文件**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: picturebook-db
    environment:
      POSTGRES_USER: picturebook
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: picturebook
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U picturebook"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: picturebook-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI后端
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: picturebook-backend
    environment:
      - DATABASE_URL=postgresql://picturebook:${DB_PASSWORD}@postgres:5432/picturebook
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: picturebook-worker
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://picturebook:${DB_PASSWORD}@postgres:5432/picturebook
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Celery Beat (定时任务)
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: picturebook-beat
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://picturebook:${DB_PASSWORD}@postgres:5432/picturebook
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Flower监控
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: picturebook-flower
    command: celery -A app.core.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 生产环境启动

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 反向代理配置

### Nginx配置

**文件**: `/etc/nginx/sites-available/picturebook`

```nginx
# HTTP重定向到HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Let's Encrypt验证
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 日志
    access_log /var/log/nginx/picturebook_access.log;
    error_log /var/log/nginx/picturebook_error.log;

    # 客户端上传大小限制
    client_max_body_size 20M;

    # API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件
    location /uploads {
        alias /path/to/ai-picture-book/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /outputs {
        alias /path/to/ai-picture-book/outputs;
        expires 7d;
        add_header Cache-Control "public";
    }

    # 前端（如果使用构建后的静态文件）
    location / {
        root /path/to/ai-picture-book/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Prometheus监控
    location /metrics {
        proxy_pass http://localhost:8000/metrics;
        allow 127.0.0.1;
        allow 10.0.0.0/8;  # 内网访问
        deny all;
    }
}
```

### 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/picturebook /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 获取SSL证书（Let's Encrypt）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 监控和维护

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 返回示例
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail=100 backend

# 查看特定时间范围
docker-compose logs --since=2024-01-01 backend

# 日志轮转配置（logrotate）
sudo vim /etc/logrotate.d/picturebook
```

**logrotate配置**:

```
/path/to/ai-picture-book/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose restart backend > /dev/null
    endscript
}
```

### Prometheus监控

**访问地址**: `http://localhost:8000/metrics`

**关键指标**:

- `http_requests_total` - HTTP请求总数
- `http_request_duration_seconds` - 请求延迟
- `books_created_total` - 创建的绘本数
- `ai_api_calls_total` - AI API调用数

### Flower监控（Celery）

**访问地址**: `http://localhost:5555`

功能：
- 查看任务队列状态
- 监控Worker性能
- 查看任务执行历史
- 重试失败任务

---

## 备份和恢复

### 数据库备份

**自动备份脚本**:

```bash
#!/bin/bash
# scripts/backup_db.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/picturebook_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec -T postgres pg_dump -U picturebook picturebook | gzip > $BACKUP_FILE

# 保留最近30天的备份
find $BACKUP_DIR -name "picturebook_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**设置定时任务**:

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/ai-picture-book/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### 文件备份

```bash
# 备份上传文件
rsync -avz /path/to/uploads/ /backups/uploads/

# 备份生成文件
rsync -avz /path/to/outputs/ /backups/outputs/
```

### 数据恢复

```bash
# 恢复数据库
gunzip -c /backups/postgres/picturebook_20240101_020000.sql.gz | \
  docker-compose exec -T postgres psql -U picturebook picturebook

# 恢复文件
rsync -avz /backups/uploads/ /path/to/uploads/
```

---

## 故障排查

### 常见问题

**1. 容器无法启动**

```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
netstat -tuln | grep 8000

# 重建容器
docker-compose up -d --force-recreate
```

**2. 数据库连接失败**

```bash
# 检查数据库状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U picturebook -c "SELECT 1"
```

**3. Celery任务不执行**

```bash
# 检查Celery状态
docker-compose logs celery-worker

# 使用Flower监控
open http://localhost:5555

# 重启Celery
docker-compose restart celery-worker
```

**4. 内存不足**

```bash
# 查看容器资源使用
docker stats

# 限制容器内存
# 在docker-compose.yml中添加:
services:
  backend:
    mem_limit: 1g
```

### 日志位置

| 服务 | 日志位置 |
|------|---------|
| 后端应用 | `./logs/backend.log` |
| Nginx | `/var/log/nginx/` |
| Docker | `docker-compose logs` |
| PostgreSQL | 容器内 `/var/log/postgresql/` |

---

## 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_books_owner ON picture_books(owner_id);
CREATE INDEX idx_books_status ON picture_books(status);

-- 定期清理旧数据
DELETE FROM book_pages WHERE created_at < NOW() - INTERVAL '1 year';
```

### Redis缓存配置

```bash
# 设置最大内存
redis-cli CONFIG SET maxmemory 256mb

# 设置淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 安全检查清单

- [ ] 更改默认的SECRET_KEY
- [ ] 配置强密码策略
- [ ] 启用HTTPS
- [ ] 配置CORS白名单
- [ ] 启用API限流
- [ ] 配置防火墙规则
- [ ] 定期更新依赖包
- [ ] 配置日志监控
- [ ] 设置自动备份
- [ ] 测试恢复流程

---

## 升级部署

```bash
# 1. 备份数据
./scripts/backup_db.sh

# 2. 拉取最新代码
git pull origin main

# 3. 构建新镜像
docker-compose build

# 4. 停止旧服务
docker-compose down

# 5. 启动新服务
docker-compose up -d

# 6. 验证部署
curl http://localhost:8000/health
```

---

**文档版本**: 1.0.0
**更新时间**: 2026-01-12
**维护者**: DevOps Team
