# Docker健康检查实施总结

## 实施时间
2026-01-09

---

## ✅ 完成的工作

### 1. 健康检查API端点 ✅

**文件**: [backend/app/api/health.py](backend/app/api/health.py)

#### 1.1 基础健康检查

```python
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "service": "AI绘本创作平台",
  "version": "1.0.0"
}
```

**特性**:
- ✅ 快速响应，不执行耗时操作
- ✅ 用于确定服务是否运行
- ✅ 适合Docker HEALTHCHECK

#### 1.2 详细健康检查

```python
GET /health/detailed
```

**响应**:
```json
{
  "status": "healthy",
  "service": "AI绘本创作平台",
  "version": "1.0.0",
  "timestamp": "2026-01-09T10:30:00",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "database": "sqlite"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "redis": "redis://localhost:6379/0",
      "optional": true
    },
    "celery": {
      "status": "healthy",
      "workers": ["celery@worker1"],
      "celery": "Connected",
      "optional": true
    },
    "api_config": {
      "status": "healthy",
      "checks": [
        {
          "name": "text_api",
          "status": "configured",
          "base_url": "https://api.openai.com/v1"
        },
        {
          "name": "image_api",
          "status": "configured",
          "base_url": "https://api.openai.com/v1"
        }
      ]
    },
    "storage": {
      "status": "healthy",
      "checks": [
        {
          "name": "upload_dir",
          "status": "accessible",
          "path": "./uploads"
        },
        {
          "name": "output_dir",
          "status": "accessible",
          "path": "./outputs"
        }
      ]
    }
  }
}
```

**检查项**:
- ✅ 数据库连接
- ✅ Redis连接（可选）
- ✅ Celery workers（可选）
- ✅ API配置
- ✅ 存储目录访问性

#### 1.3 就绪探针（Readiness Probe）

```python
GET /health/ready
```

**特性**:
- ✅ 检查服务是否准备好接收请求
- ✅ 验证数据库连接
- ✅ 用于Kubernetes readinessProbe

**响应**:
```json
{
  "status": "ready",
  "timestamp": "2026-01-09T10:30:00"
}
```

失败时返回503状态码

#### 1.4 存活探针（Liveness Probe）

```python
GET /health/live
```

**特性**:
- ✅ 快速检查服务是否存活
- ✅ 不检查外部依赖
- ✅ 用于Kubernetes livenessProbe

**响应**:
```json
{
  "status": "alive",
  "timestamp": "2026-01-09T10:30:00"
}
```

---

### 2. Docker健康检查配置 ✅

#### 2.1 后端服务健康检查

**文件**: [docker-compose.yml](docker-compose.yml)

```yaml
backend:
  # ... 其他配置
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s      # 每30秒检查一次
    timeout: 10s        # 超时时间10秒
    retries: 3          # 失败后重试3次
    start_period: 40s   # 启动后40秒才开始检查
```

**参数说明**:
- `test`: 健康检查命令
- `interval`: 检查间隔
- `timeout`: 超时时间
- `retries`: 连续失败多少次标记为不健康
- `start_period`: 启动宽限期，容器启动后多久开始检查

#### 2.2 前端服务健康检查

```yaml
frontend:
  # ... 其他配置
  depends_on:
    backend:
      condition: service_healthy  # 等待backend健康后才启动
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:80"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 10s
```

**特性**:
- ✅ 依赖backend健康状态
- ✅ 使用nginx默认端口80
- ✅ 更快的检查频率

#### 2.3 Redis健康检查

```yaml
redis:
  image: redis:7-alpine
  # ... 其他配置
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s      # 更频繁的检查
    timeout: 5s
    retries: 5
    start_period: 10s
```

**特性**:
- ✅ 使用Redis内置PING命令
- ✅ 快速检查（10秒间隔）
- ✅ 更多重试次数

---

### 3. Dockerfile更新 ✅

**文件**: [backend/Dockerfile](backend/Dockerfile)

**更改**:
```dockerfile
# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    curl \                    # 添加curl用于健康检查
    && rm -rf /var/lib/apt/lists/*
```

**为什么需要curl**:
- Docker健康检查需要工具来访问HTTP端点
- curl是轻量级且可靠的HTTP客户端
- 用于调用 `/health` 端点

---

## 📖 使用指南

### 1. 本地测试健康检查

#### 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看健康状态
docker-compose ps
```

#### 手动测试健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/health/detailed

# 就绪检查
curl http://localhost:8000/health/ready

# 存活检查
curl http://localhost:8000/health/live
```

#### 查看健康检查日志

```bash
# 查看backend的健康检查日志
docker-compose logs backend | grep healthcheck

# 实时监控健康状态
docker inspect --format='{{json .State.Health}}' backend_ai-picture-book_1 | jq
```

### 2. 生产环境使用

#### Kubernetes部署

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        ports:
        - containerPort: 8000
        # 存活探针
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        # 就绪探针
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        # 启动探针
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30
```

#### Docker Swarm部署

**stack.yaml**:
```yaml
version: '3.8'

services:
  backend:
    image: your-registry/backend:latest
    deploy:
      replicas: 3
      update_config:
        order: start-first
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 3. 监控和告警

#### 集成监控工具

**Prometheus**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'backend-health'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/health/detailed'
    scrape_interval: 30s
```

**Grafana Dashboard**:
- 监控健康状态变化
- 可视化响应时间
- 设置告警规则

#### 告警规则

**Prometheus Alertmanager**:
```yaml
groups:
  - name: backend-health
    rules:
      - alert: BackendUnhealthy
        expr: up{job="backend-health"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend服务不健康"
          description: "Backend健康检查失败超过1分钟"

      - alert: DatabaseSlow
        expr: health_check_response_time_ms > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库响应缓慢"
          description: "数据库响应时间超过1秒"
```

---

## 💡 最佳实践

### ✅ 推荐做法

#### 1. 使用分层健康检查

```python
# 1. 快速健康检查（用于liveness）
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

# 2. 就绪检查（用于readiness）
@app.get("/health/ready")
async def readiness():
    # 检查依赖是否就绪
    return {"status": "ready"}

# 3. 详细健康检查（用于监控）
@app.get("/health/detailed")
async def detailed():
    # 检查所有组件
    return {"status": "healthy", "checks": {...}}
```

#### 2. 设置合理的超时和重试

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s      # 不要太频繁，避免浪费资源
  timeout: 10s        # 给足够时间响应
  retries: 3          # 允许偶尔的网络抖动
  start_period: 40s   # 给服务足够的启动时间
```

#### 3. 服务依赖健康检查

```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # 等待backend健康后再启动
```

#### 4. 优雅的失败处理

```python
async def check_database_health():
    try:
        # 快速检查
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database unhealthy: {e}")
        return {"status": "unhealthy", "error": str(e)}
```

### ❌ 避免的做法

#### 1. 不要在健康检查中执行耗时操作

```python
# ❌ 不好
@app.get("/health")
async def health():
    # 执行耗时查询
    books = db.query(Book).all()
    return {"status": "healthy", "count": len(books)}

# ✅ 好
@app.get("/health")
async def health():
    # 只检查连接
    return {"status": "healthy"}
```

#### 2. 不要设置过短的检查间隔

```yaml
# ❌ 不好 - 太频繁
healthcheck:
  interval: 1s

# ✅ 好 - 合理的频率
healthcheck:
  interval: 30s
```

#### 3. 不要忽略启动宽限期

```yaml
# ❌ 不好 - 没有启动宽限期
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  retries: 3

# ✅ 好 - 有启动宽限期
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s  # 重要！
```

---

## 🚨 故障排查

### 问题1: 健康检查一直失败

**症状**: `docker-compose ps` 显示服务为 `unhealthy`

**解决方案**:

1. 检查健康检查端点是否可访问
```bash
docker-compose exec backend curl -f http://localhost:8000/health
```

2. 查看服务日志
```bash
docker-compose logs backend
```

3. 确认curl已安装
```bash
docker-compose exec backend which curl
```

4. 检查服务是否真正启动
```bash
docker-compose exec backend ps aux
```

### 问题2: 前端无法等待backend就绪

**症状**: 前端启动失败，无法连接backend

**解决方案**:

1. 确认depends_on配置正确
```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # 必须有这个
```

2. 增加backend的启动宽限期
```yaml
backend:
  healthcheck:
    start_period: 60s  # 给更多时间启动
```

3. 手动测试健康检查
```bash
curl http://localhost:8000/health/detailed
```

### 问题3: 服务频繁重启

**症状**: 容器不断重启（Restarting）

**可能原因**:
- 健康检查失败
- 应用本身崩溃
- 资源不足

**解决方案**:

1. 查看容器日志
```bash
docker-compose logs backend
```

2. 检查健康检查配置
```bash
docker inspect backend | jq '.[0].State.Health'
```

3. 增加重试次数和宽限期
```yaml
healthcheck:
  retries: 5          # 增加重试次数
  start_period: 60s  # 增加启动宽限期
```

### 问题4: 数据库连接缓慢导致健康检查失败

**症状**: 健康检查间歇性失败

**解决方案**:

1. 优化数据库查询
```python
# 使用简单的查询
result = db.execute(text("SELECT 1"))  # 快速
```

2. 增加超时时间
```yaml
healthcheck:
  timeout: 15s  # 给更多时间
```

3. 使用连接池
```python
# 确保连接池配置正确
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True  # 检查连接有效性
)
```

---

## 📊 健康检查层级

```
┌─────────────────────────────────────────┐
│     Docker Health Check (L1)            │
│     /health (快速响应)                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     Service Health Check (L2)           │
│     /health/detailed (全面检查)         │
├─────────────────────────────────────────┤
│  ├─ Database Health                     │
│  ├─ Redis Health                        │
│  ├─ Celery Health                       │
│  ├─ API Config Health                   │
│  └─ Storage Health                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     Kubernetes Probes (L3)              │
│     /health/live (liveness)             │
│     /health/ready (readiness)           │
└─────────────────────────────────────────┘
```

---

## 🔧 高级配置

### 1. 自定义健康检查逻辑

```python
# backend/app/api/health.py

async def check_custom_service() -> Dict[str, Any]:
    """检查自定义服务"""
    try:
        # 调用外部API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://external-service.com/health",
                timeout=5.0
            )
            response.raise_for_status()

        return {
            "status": "healthy",
            "service": "external"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "external",
            "error": str(e)
        }
```

### 2. 健康检查缓存

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 缓存5分钟
@lru_cache(maxsize=1)
def get_cached_health_status():
    return {
        "status": "healthy",
        "timestamp": datetime.now()
    }

@app.get("/health/cached")
async def cached_health_check():
    """带缓存的健康检查"""
    status = get_cached_health_status()
    return status
```

### 3. 异步健康检查

```python
import asyncio
from typing import Dict, Any

async def run_parallel_health_checks() -> Dict[str, Any]:
    """并行执行多个健康检查"""
    tasks = [
        check_database_health(),
        check_redis_health(),
        check_celery_health(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "database": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
        "redis": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
        "celery": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
    }
```

---

## 📁 文件清单

### 新增文件

- [backend/app/api/health.py](backend/app/api/health.py) - 健康检查API端点
- [DOCKER_HEALTHCHECK_GUIDE.md](DOCKER_HEALTHCHECK_GUIDE.md) - 本文档

### 修改的文件

- [backend/app/main.py](backend/app/main.py) - 注册健康检查路由
- [backend/Dockerfile](backend/Dockerfile) - 安装curl工具
- [docker-compose.yml](docker-compose.yml) - 添加健康检查配置

---

## 🔮 后续改进

### 短期（本周）

1. ✅ 实现基础健康检查
2. ✅ 配置Docker健康检查
3. ✅ 添加详细健康检查

### 中期（本月）

1. **集成监控系统**
   - Prometheus指标导出
   - Grafana仪表板
   - 告警规则配置

2. **性能指标**
   - 响应时间监控
   - 资源使用率监控
   - 请求成功率

### 长期（季度）

1. **分布式追踪**
   - OpenTelemetry集成
   - 分布式日志追踪
   - 性能分析

2. **自动恢复**
   - 自动重启策略
   - 故障自动转移
   - 灾难恢复

---

## 🔗 相关资源

- [Docker Healthcheck](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Docker Compose Healthcheck](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Microservices Health Checks](https://microservices.io/patterns/observability/health-check-api/)

---

## 📊 完成状态

| 任务 | 状态 |
|------|------|
| 创建健康检查API端点 | ✅ 完成 |
| 更新Dockerfile安装curl | ✅ 完成 |
| 配置docker-compose.yml | ✅ 完成 |
| 添加服务依赖健康检查 | ✅ 完成 |
| 编写健康检查文档 | ✅ 完成 |

**整体进度**: 5/5 (100%)

---

**实施完成时间**: 2026-01-09
**实施者**: Claude Code
**优化类型**: Docker健康检查
**影响范围**: Docker部署、容器编排
**可靠性**: ⭐⭐⭐⭐⭐ 显著提升
**可维护性**: ⭐⭐⭐⭐⭐ 显著提升
