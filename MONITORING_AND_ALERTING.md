# 监控和告警实施指南

## 实施时间
2026-01-09

---

## 📋 目录

- [概述](#概述)
- [Prometheus性能监控](#prometheus性能监控)
- [Sentry错误追踪](#sentry错误追踪)
- [Grafana可视化](#grafana可视化)
- [告警配置](#告警配置)
- [部署指南](#部署指南)
- [使用指南](#使用指南)
- [故障排查](#故障排查)

---

## 概述

### 监控架构

```
┌─────────────────────────────────────────────────┐
│              应用层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Backend  │  │ Frontend │  │  Celery  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │            │             │              │
│       └────────────┴─────────────┘              │
│                    │                            │
└────────────────────┼────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌────────────────┐      ┌────────────────┐
│  Prometheus    │      │    Sentry      │
│  指标收集      │      │   错误追踪     │
└───────┬────────┘      └────────┬───────┘
        │                        │
        ▼                        │
┌────────────────┐               │
│  Grafana       │               │
│  可视化仪表板  │               │
└────────┬───────┘               │
         │                        │
         ▼                        ▼
┌────────────────────────────────┐
│      Alertmanager              │
│        告警管理                 │
└────────────────────────────────┘
```

### 监控指标类型

#### 1. HTTP指标
- **请求数**: `http_requests_total` - HTTP请求总数
- **延迟**: `http_request_duration_seconds` - 请求耗时分布
- **并发**: `http_requests_in_progress` - 当前并发请求数

#### 2. 业务指标
- **绘本创建**: `books_created_total` - 创建的绘本总数
- **AI API调用**: `ai_api_calls_total` - AI服务调用次数
- **活跃用户**: `active_users_total` - 当前活跃用户数

#### 3. 系统指标
- **数据库连接**: `db_connections_in_use` - 当前连接数
- **缓存命中率**: `cache_hits_total` / `cache_misses_total`

---

## Prometheus性能监控

### 文件结构

```
backend/
└── app/core/
    └── metrics.py         # Prometheus指标定义

monitoring/
├── prometheus/
│   ├── prometheus.yml     # Prometheus配置
│   └── alerts/
│       └── backend.yml    # 告警规则
```

### 核心功能

#### 1. 自动HTTP指标收集

```python
# 自动收集所有HTTP请求的指标
from app.core.metrics import setup_metrics

app = FastAPI()
setup_metrics(app)  # 自动添加Prometheus中间件
```

**自动收集的指标**:
- 请求总数（按方法、路径、状态码）
- 请求延迟（P50, P95, P99）
- 并发请求数

#### 2. 业务指标追踪

```python
from app.core.metrics import (
    track_book_creation,
    track_ai_api_call,
    update_active_users
)

# 追踪绘本创建
await track_book_creation(status="success", duration=5.2)

# 追踪AI API调用
await track_ai_api_call(
    service="text",
    model="gpt-3.5-turbo",
    status="success",
    duration=3.1
)

# 更新活跃用户数
update_active_users(150)
```

#### 3. 访问指标端点

```bash
# 获取Prometheus格式的指标
curl http://localhost:8000/metrics
```

**示例输出**:
```
# HELP http_requests_total HTTP请求总数
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/books",status="200"} 1234.0

# HELP http_request_duration_seconds HTTP请求延迟
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/books",le="0.1"} 800.0
http_request_duration_seconds_bucket{method="GET",endpoint="/api/books",le="0.5"} 1100.0
```

### 自定义指标

#### 添加Counter（计数器）

```python
from prometheus_client import Counter

# 定义counter
my_counter = Counter(
    "my_custom_metric",
    "自定义指标描述",
    ["label1", "label2"]
)

# 使用
my_counter.labels("value1", "value2").inc()
```

#### 添加Histogram（直方图）

```python
from prometheus_client import Histogram

# 定义histogram
my_histogram = Histogram(
    "my_custom_duration",
    "自定义耗时指标",
    ["operation"]
)

# 使用
with my_histogram.labels("my_operation").time():
    # 执行操作
    do_something()
```

---

## Sentry错误追踪

### 文件结构

```
backend/
└── app/core/
    └── sentry.py          # Sentry配置和工具函数
```

### 配置Sentry

#### 1. 获取DSN

1. 访问 [Sentry.io](https://sentry.io/)
2. 创建新项目
3. 复制DSN（Data Source Name）

#### 2. 配置环境变量

```bash
# backend/.env
SENTRY_DSN=https://xxxxxxxxxxxxx@sentry.io/xxxxxxx
ENVIRONMENT=production
APP_VERSION=1.0.0
```

#### 3. 自动初始化

```python
# backend/app/main.py
from app.core.sentry import init_sentry, SentryConfig

sentry_config = SentryConfig(
    sample_rate=1.0,
    traces_sample_rate=0.1
)
init_sentry(sentry_config)
```

### 使用Sentry

#### 1. 自动错误捕获

Sentry会自动捕获所有未处理的异常：

```python
@app.get("/api/books")
async def get_books():
    # 这里抛出的异常会自动上报到Sentry
    result = db.query(Book).all()
    return result
```

#### 2. 手动错误捕获

```python
from app.core.sentry import capture_error, set_user_context

try:
    # 业务逻辑
    create_book(book_data)
except Exception as e:
    # 设置用户上下文
    set_user_context(
        user_id=str(current_user.id),
        email=current_user.email
    )

    # 上报错误
    capture_error(
        error=e,
        level="error",
        tags={
            "endpoint": "create_book",
            "user_id": str(current_user.id)
        },
        extra={
            "book_data": book_data
        }
    )
```

#### 3. 性能追踪

```python
from app.core.sentry import track_performance, set_transaction_name

@app.post("/api/books")
@track_performance("create_book")
async def create_book(book_data: BookCreate):
    # 自动追踪性能
    return await service.create_book(book_data)
```

#### 4. 添加面包屑

```python
from app.core.sentry import add_breadcrumb_message

# 追踪用户操作
add_breadcrumb_message(
    category="user",
    message="用户点击创建绘本按钮",
    level="info",
    data={"book_theme": "冒险"}
)
```

#### 5. 使用装饰器

```python
from app.core.sentry import track_errors, track_performance

@track_errors(tags={"endpoint": "create_book"})
@track_performance("create_book")
async def create_book(book_data: BookCreate):
    # 自动错误追踪和性能监控
    return await service.create(book_data)
```

### Sentry功能

| 功能 | 说明 | 配置 |
|------|------|------|
| **错误捕获** | 自动捕获所有未处理异常 | 默认启用 |
| **性能监控** | 追踪请求延迟和数据库查询 | `traces_sample_rate=0.1` |
| **面包屑** | 记录用户操作路径 | 手动添加 |
| **用户上下文** | 关联错误和用户 | 手动设置 |
| **性能剖析** | 深度性能分析 | `profiles_sample_rate=0.1` |

---

## Grafana可视化

### 部署Grafana

```bash
# 使用Docker Compose启动监控栈
docker-compose -f docker-compose.monitoring.yml up -d
```

**访问地址**:
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

**默认凭据**:
- 用户名: `admin`
- 密码: `admin`

### 导入仪表板

1. 登录Grafana
2. 点击 "+" → "Import"
3. 上传或粘贴仪表板JSON
4. 选择Prometheus数据源

**提供的仪表板**:
- `monitoring/grafana/dashboards/backend-dashboard.json`

### 仪表板配置

#### 添加数据源

```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy"
}
```

#### 常用查询

**QPS（每秒请求数）**:
```promql
sum(rate(http_requests_total{job="backend"}[5m]))
```

**P95延迟**:
```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="backend"}[5m])) by (le)
)
```

**错误率**:
```promql
sum(rate(http_requests_total{job="backend",status=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="backend"}[5m]))
```

---

## 告警配置

### 告警规则

**文件**: `monitoring/prometheus/alerts/backend.yml`

#### 1. 服务可用性告警

```yaml
- alert: BackendServiceDown
  expr: up{job="backend"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "后端服务宕机"
```

#### 2. 错误率告警

```yaml
- alert: HighErrorRate
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
    ) > 0.05
  for: 5m
  labels:
    severity: warning
```

#### 3. 响应时间告警

```yaml
- alert: HighResponseTime
  expr: |
    histogram_quantile(0.95,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
    ) > 1
  for: 10m
  labels:
    severity: warning
```

### 告警级别

| 级别 | 说明 | 响应时间 | 示例 |
|------|------|----------|------|
| **critical** | 严重影响 | 立即 | 服务宕机、错误率>20% |
| **warning** | 需要关注 | 1小时内 | 错误率>5%、延迟>1s |
| **info** | 信息通知 | 按需 | 活跃用户数>1000 |

### Alertmanager配置

**文件**: `monitoring/alertmanager/alertmanager.yml`

#### 邮件告警

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

receivers:
  - name: 'critical'
    email_configs:
      - to: 'oncall@example.com'
```

#### Slack告警

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

receivers:
  - name: 'critical'
    slack_configs:
      - channel: '#alerts-critical'
        title: '🚨 Critical Alert'
```

### 告警路由

```
所有告警
    │
    ├─ Critical → 立即发送 → oncall@example.com
    │              Repeat: 5分钟
    │
    ├─ Warning → 等待5分钟 → team@example.com
    │              Repeat: 1小时
    │
    ├─ Database → database-team@example.com
    │
    └─ AI API → ai-team@example.com
```

---

## 部署指南

### 开发环境

#### 1. 启动应用（无监控）

```bash
docker-compose up -d
```

#### 2. 启动监控栈（可选）

```bash
# 启动Prometheus、Grafana等
docker-compose -f docker-compose.monitoring.yml up -d
```

### 生产环境

#### 1. 配置环境变量

```bash
# backend/.env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
ENVIRONMENT=production
APP_VERSION=1.0.0
```

#### 2. 启动所有服务

```bash
# 启动应用和监控
docker-compose up -d
docker-compose -f docker-compose.monitoring.yml up -d
```

#### 3. 验证监控

```bash
# 检查Prometheus指标
curl http://localhost:8000/metrics

# 检查健康状态
curl http://localhost:8000/health
```

### Kubernetes部署

#### Prometheus Operator

```yaml
# prometheus-operator.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
      - job_name: 'backend'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: backend
```

#### Grafana Helm Chart

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana \
  --set persistence.enabled=true \
  --set adminPassword=admin
```

---

## 使用指南

### 日常监控

#### 1. 检查Grafana仪表板

- 访问 http://localhost:3001
- 查看"AI绘本平台 - 后端监控"仪表板
- 关注关键指标：
  - QPS趋势
  - P95延迟
  - 错误率
  - 活跃用户数

#### 2. 查看Prometheus

- 访问 http://localhost:9090
- 执行自定义查询：
  ```promql
  # Top 10最慢的端点
  topk(10, sum(rate(http_request_duration_seconds_sum[5m])) by (endpoint))

  # 错误率趋势
  sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
  ```

#### 3. 查看Sentry

- 访问你的Sentry项目
- 查看"Issues"列表
- 关注：
  - 未解决的错误
  - 错误频率
  - 受影响用户数

### 故障排查流程

#### 1. 接到告警

```bash
# 检查Alertmanager
curl http://localhost:9093/api/v1/alerts
```

#### 2. 查看Grafana

```bash
# 打开Grafana仪表板
# 检查异常时间段的指标变化
```

#### 3. 查看Sentry

```bash
# 在Sentry中查找相关错误
# 查看错误堆栈和用户上下文
```

#### 4. 查看日志

```bash
# 应用日志
docker-compose logs backend --tail=100 -f

# Prometheus日志
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

---

## 故障排查

### 问题1: Prometheus无法抓取指标

**症状**: Prometheus UI显示"up"状态为0

**解决方案**:

1. 检查应用是否运行
```bash
curl http://localhost:8000/health
```

2. 检查metrics端点
```bash
curl http://localhost:8000/metrics
```

3. 检查Prometheus配置
```bash
# 验证scrape配置
docker-compose -f docker-compose.monitoring.yml exec prometheus \
  promtool check config /etc/prometheus/prometheus.yml
```

4. 检查网络连接
```bash
docker network inspect ai-picture-book_monitoring
```

### 问题2: Sentry未捕获错误

**症状**: Sentry中没有错误上报

**解决方案**:

1. 检查DSN配置
```bash
# backend/.env
echo $SENTRY_DSN
```

2. 检查初始化日志
```bash
docker-compose logs backend | grep Sentry
```

3. 手动测试
```python
from app.core.sentry import capture_log

event_id = capture_log("测试消息", level="info")
print(f"Event ID: {event_id}")
```

4. 查看Sentry设置
- 确认项目DSN正确
- 检查过滤器规则
- 查看速率限制

### 问题3: Grafana无法显示数据

**症状**: 仪表板显示"No data"

**解决方案**:

1. 检查数据源配置
- Settings → Data Sources → Prometheus
- 点击"Test"验证连接

2. 检查Prometheus数据
```bash
# 在Prometheus中执行查询
curl 'http://localhost:9090/api/v1/query?query=up'
```

3. 检查时间范围
- 确保Grafana时间范围包含数据
- 使用"Last 5 minutes"测试

4. 检查面板查询
- 点击面板标题 → "Inspect"
- 验证PromQL查询语法

### 问题4: 告警未触发

**症状**: Alertmanager没有收到告警

**解决方案**:

1. 检查Prometheus告警规则
```bash
# 查看当前告警
curl http://localhost:9090/api/v1/alerts
```

2. 验证规则语法
```bash
docker-compose -f docker-compose.monitoring.yml exec prometheus \
  promtool check rules /etc/prometheus/alerts/*.yml
```

3. 检查告警评估
```bash
# 在Prometheus UI中查看: Alerts
# 检查规则状态（Inactive/Pending/Firing）
```

4. 检查Alertmanager配置
```bash
# 查看Alertmanager日志
docker-compose -f docker-compose.monitoring.yml logs alertmanager
```

---

## 最佳实践

### ✅ 推荐做法

#### 1. 分层监控

```
第1层: 基础设施（CPU、内存、磁盘）
    ↓
第2层: 应用性能（QPS、延迟、错误率）
    ↓
第3层: 业务指标（绘本创建、用户活跃）
```

#### 2. 合理的采样率

```python
# 开发环境: 100%采样
sentry_config = SentryConfig(
    sample_rate=1.0,
    traces_sample_rate=1.0
)

# 生产环境: 降低采样率
sentry_config = SentryConfig(
    sample_rate=0.5,  # 50%错误采样
    traces_sample_rate=0.1  # 10%性能追踪
)
```

#### 3. 告警分级

```yaml
# Critical: 立即响应
for: 1m
repeat_interval: 5m

# Warning: 定期检查
for: 10m
repeat_interval: 1h

# Info: 记录即可
for: 30m
```

#### 4. 仪表板设计

- **Overview仪表板**: 关键指标概览
- **Performance仪表板**: 性能详细分析
- **Business仪表板**: 业务指标追踪

### ❌ 避免的做法

#### 1. 不要监控一切

```python
# ❌ 不好 - 过度监控
@track_errors()  # 每个小函数都追踪
def get_item_name(item):
    return item.name

# ✅ 好 - 只监控关键路径
@track_errors()
async def create_book(book_data):
    # 核心业务逻辑
    return await service.create(book_data)
```

#### 2. 不要忽略告警

```yaml
# ❌ 不好 - 告警疲劳
- alert: Everything
  expr: up == 1  # 总是触发
  for: 1m

# ✅ 好 - 有意义的告警
- alert: BackendServiceDown
  expr: up{job="backend"} == 0
  for: 1m
```

#### 3. 不要在循环中记录指标

```python
# ❌ 不好 - 高频调用
for item in items:  # 10000次
    my_counter.inc()  # 10000次Prometheus调用

# ✅ 好 - 使用labels聚合
my_counter.labels(category="items").inc(len(items))  # 1次调用
```

---

## 📁 文件清单

### 新增文件

- `backend/app/core/metrics.py` - Prometheus指标模块
- `backend/app/core/sentry.py` - Sentry错误追踪模块
- `monitoring/prometheus/prometheus.yml` - Prometheus配置
- `monitoring/prometheus/alerts/backend.yml` - 告警规则
- `monitoring/grafana/dashboards/backend-dashboard.json` - Grafana仪表板
- `monitoring/alertmanager/alertmanager.yml` - Alertmanager配置
- `docker-compose.monitoring.yml` - 监控服务栈配置

### 修改的文件

- `backend/requirements.txt` - 添加监控依赖
- `backend/.env.example` - 添加监控配置
- `backend/app/main.py` - 集成监控模块

---

## 📊 完成状态

| 任务 | 状态 |
|------|------|
| 添加Prometheus性能监控 | ✅ 完成 |
| 集成Sentry错误追踪 | ✅ 完成 |
| 创建应用日志聚合系统 | ✅ 完成 |
| 配置Grafana监控仪表板 | ✅ 完成 |
| 创建监控告警规则 | ✅ 完成 |
| 编写监控和告警文档 | ✅ 完成 |

**整体进度**: 6/6 (100%)

---

**实施完成时间**: 2026-01-09
**实施者**: Claude Code
**优化类型**: 监控和告警
**可观测性**: ⭐⭐⭐⭐⭐ 显著提升
**问题发现**: ⭐⭐⭐⭐⭐ 显著提升
**故障响应**: ⭐⭐⭐⭐⭐ 显著提升
