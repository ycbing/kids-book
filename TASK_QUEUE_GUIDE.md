# Celery任务队列实施总结

## 实施时间
2026-01-08

---

## ✅ 完成的工作

### 1. Celery应用配置 ✅

**文件**: [backend/app/core/celery_app.py](backend/app/core/celery_app.py)

**核心配置**:
```python
celery_app = Celery(
    "ai_picture_book",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)
```

**关键配置项**:
- **序列化**: JSON格式
- **超时**: 任务1小时，软超时55分钟
- **重试**: 最多3次，指数退避
- **并发**: 2个worker
- **任务追踪**: 启用

---

### 2. 异步任务实现 ✅

**文件**: [backend/app/services/book_tasks.py](backend/app/services/book_tasks.py)

**实现的任务**:

#### 2.1 绘本生成任务

**任务名**: `app.tasks.generate_book_content`

**功能**:
- 异步生成绘本故事和配图
- 实时进度报告
- 失败自动重试
- 数据库事务管理

**进度报告**:
```python
{
    'stage': 'generating_story',     # 当前阶段
    'progress': 10,                   # 进度百分比
    'message': '正在生成故事文本...',  # 状态消息
    'current_page': 1,                # 当前页码
    'total_pages': 8                  # 总页数
}
```

**任务流程**:
```
1. 初始化 (0%)
   ↓
2. 生成故事 (10-30%)
   ↓
3. 生成配图 (30-90%)
   ↓
4. 保存内容 (90-100%)
   ↓
5. 完成 (100%)
```

#### 2.2 配图重新生成任务

**任务名**: `app.tasks.regenerate_page_image`

**功能**:
- 单页配图重新生成
- 异步执行，不阻塞API
- 返回新的图片URL

#### 2.3 清理任务

**任务名**: `app.tasks.cleanup_old_books`

**功能**:
- 定期清理旧草稿
- 释放数据库空间
- 可配置保留天数

---

### 3. API端点改造 ✅

**修改文件**: [backend/app/api/routes.py](backend/app/api/routes.py)

**改造前** (使用BackgroundTasks):
```python
@router.post("/books")
async def create_book(
    request: BookCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    book = await book_service.create_book(db, request, user_id)
    background_tasks.add_task(
        book_service.generate_book_content,
        db, book.id, request, None, manager
    )
    return book_service.get_book(db, book.id)
```

**改造后** (使用Celery):
```python
@router.post("/books")
async def create_book(
    request: BookCreateRequest,
    db: Session = Depends(get_db)
):
    book = await book_service.create_book(db, request, user_id)

    # 启动Celery异步任务
    task = generate_book_content_task.delay(
        book_id=book.id,
        request_data=request.dict(),
        user_id=user_id
    )

    return {
        "book_id": book.id,
        "task_id": task.id,
        "status": "generating",
        "message": "绘本已创建，正在生成内容..."
    }
```

**改造后的端点**:
- `POST /books` - 创建绘本（使用Celery）
- `POST /books/{id}/regenerate-image/{page}` - 重新生成配图（使用Celery）

---

### 4. 任务状态查询API ✅

**新增端点**:

#### 4.1 查询任务状态

```
GET /api/v1/tasks/{task_id}
```

**响应示例**:
```json
{
  "task_id": "abc-123-def",
  "status": "PROGRESS",
  "message": "任务进行中...",
  "progress": {
    "stage": "generating_images",
    "progress": 45,
    "message": "正在生成第 3/8 张配图...",
    "current_page": 3,
    "total_pages": 8
  }
}
```

#### 4.2 取消任务

```
POST /api/v1/tasks/{task_id}/cancel
```

**响应示例**:
```json
{
  "task_id": "abc-123-def",
  "status": "cancelled",
  "message": "任务已取消"
}
```

---

### 5. Worker启动脚本 ✅

**Linux/Mac**: [backend/start_celery.sh](backend/start_celery.sh)
```bash
#!/bin/bash
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=solo
```

**Windows**: [backend/start_celery.bat](backend/start_celery.bat)
```batch
celery -A app.core.celery_app worker --loglevel=info --concurrency=1 --pool=solo
```

---

## 📊 优化效果

### 修改前

**问题**:
- ❌ 使用FastAPI的BackgroundTasks
- ❌ 服务重启会丢失任务
- ❌ 无法追踪任务进度
- ❌ 无法横向扩展
- ❌ 长时间任务导致请求超时

### 修改后

**优势**:
- ✅ 使用专业的任务队列
- ✅ 任务持久化，服务重启不丢失
- ✅ 实时进度追踪
- ✅ 支持分布式部署
- ✅ 异步执行，API响应快
- ✅ 自动重试机制
- ✅ 任务监控和管理

---

## 📖 使用指南

### 1. 启动Redis

```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS
brew services start redis

# Windows (使用WSL)
sudo service redis-server start

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. 启动Celery Worker

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

**手动启动**:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

### 3. 启动FastAPI服务器

```bash
cd backend
python -m app.main
```

### 4. 使用Celery任务

**创建绘本**:
```bash
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "小兔子学会分享",
    "keywords": ["友谊", "分享"],
    "target_age": "3-6岁",
    "style": "水彩风格",
    "page_count": 8
  }'
```

**响应**:
```json
{
  "book_id": 123,
  "task_id": "abc-123-def",
  "status": "generating",
  "message": "绘本已创建，正在生成内容..."
}
```

**查询任务状态**:
```bash
curl http://localhost:8000/api/v1/tasks/abc-123-def
```

**取消任务**:
```bash
curl -X POST http://localhost:8000/api/v1/tasks/abc-123-def/cancel
```

---

## 🔧 配置说明

### Celery配置

**位置**: [backend/app/core/celery_app.py](backend/app/core/celery_app.py)

**重要参数**:
```python
task_time_limit=3600        # 硬超时：1小时
task_soft_time_limit=3300    # 软超时：55分钟
task_retry_max_times=3       # 最多重试3次
worker_concurrency=2         # 并发worker数
worker_max_tasks_per_child=50  # 每个worker处理50个任务后重启
```

### Redis配置

**位置**: [backend/.env](backend/.env)

```env
# Redis配置（Celery必需）
REDIS_URL=redis://localhost:6379/0
```

---

## 🎯 Celery vs BackgroundTasks对比

| 特性 | BackgroundTasks | Celery |
|------|----------------|--------|
| **持久化** | ❌ 服务重启丢失 | ✅ 任务持久化 |
| **分布式** | ❌ 单机 | ✅ 支持多worker |
| **进度追踪** | ❌ 无 | ✅ 实时进度 |
| **任务管理** | ❌ 无 | ✅ 撤销/重试 |
| **定时任务** | ❌ 不支持 | ✅ Celery Beat |
| **监控** | ❌ 无 | ✅ Flower |
| **复杂度** | ✅ 简单 | ⚠️ 需要额外配置 |

---

## 📈 任务状态

| 状态 | 说明 |
|------|------|
| `PENDING` | 任务等待执行 |
| `STARTED` | 任务已开始 |
| `PROGRESS` | 任务进行中（有进度信息） |
| `SUCCESS` | 任务成功完成 |
| `FAILURE` | 任务失败 |
| `REVOKED` | 任务已取消 |
| `RETRY` | 任务重试中 |

---

## 🔍 监控和调试

### 1. Celery日志

**位置**: `backend/celery.log`

**查看实时日志**:
```bash
tail -f backend/celery.log
```

### 2. Flower监控（推荐）

**安装**:
```bash
pip install flower
```

**启动**:
```bash
celery -A app.core.celery_app flower --port=5555
```

**访问**: http://localhost:5555

**功能**:
- 实时任务监控
- Worker状态
- 任务统计
- 任务追踪

### 3. 命令行检查

**检查worker状态**:
```bash
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect registered
celery -A app.core.celery_app inspect stats
```

---

## 🚨 常见问题

### 1. Redis连接失败

**症状**:
```
Error: Error 111 connecting to localhost:6379. Connection refused.
```

**解决**:
```bash
# 检查Redis是否运行
redis-cli ping

# 启动Redis
sudo systemctl start redis-server
```

### 2. Worker没有接收到任务

**症状**: 任务状态一直是PENDING

**排查**:
1. 检查worker是否启动
2. 查看worker日志
3. 确认任务名称正确

```bash
# 查看已注册的任务
celery -A app.core.celery_app inspect registered
```

### 3. 任务执行失败

**症状**: 任务状态为FAILURE

**排查**:
1. 查看worker日志中的错误堆栈
2. 检查数据库连接
3. 验证API密钥配置

```bash
# 查看任务详情
celery -A app.core.celery_app inspect query_task
```

### 4. 内存泄漏

**症状**: Worker内存持续增长

**解决**:
- 已配置 `worker_max_tasks_per_child=50`
- Worker会在处理50个任务后自动重启

---

## 📁 文件清单

### 新增文件

**核心模块**:
- [backend/app/core/celery_app.py](backend/app/core/celery_app.py) - Celery应用配置

**任务定义**:
- [backend/app/services/book_tasks.py](backend/app/services/book_tasks.py) - 绘本生成任务

**启动脚本**:
- [backend/start_celery.sh](backend/start_celery.sh) - Linux/Mac启动脚本
- [backend/start_celery.bat](backend/start_celery.bat) - Windows启动脚本

**文档**:
- [TASK_QUEUE_GUIDE.md](TASK_QUEUE_GUIDE.md) - 本文档

### 修改的文件

- [backend/app/api/routes.py](backend/app/api/routes.py)
  - 修改 `POST /books` 使用Celery
  - 修改 `POST /books/{id}/regenerate-image/{page}` 使用Celery
  - 新增 `GET /tasks/{task_id}` 任务状态查询
  - 新增 `POST /tasks/{task_id}/cancel` 取消任务

- [backend/requirements.txt](backend/requirements.txt)
  - Celery已存在（5.3.4+）

---

## 💡 最佳实践

### ✅ 推荐做法

1. **使用Celery处理长时间任务**
   - 绘本生成（2-5分钟）
   - 批量导出
   - 图片处理

2. **合理设置任务超时**
   - 根据实际执行时间
   - 避免无限期等待

3. **启用任务重试**
   - 网络错误自动重试
   - 限制重试次数

4. **定期清理旧任务**
   - 使用cleanup任务
   - 避免结果存储膨胀

5. **监控Worker状态**
   - 使用Flower
   - 定期检查日志

### ❌ 避免的做法

1. **不要在任务中使用大量内存**
   - 分批处理大数据
   - 及时释放资源

2. **不要在任务中进行同步I/O**
   - 使用异步库
   - 避免阻塞worker

3. **不要忽略任务失败**
   - 实现错误处理
   - 记录失败原因

4. **不要使用无限循环的任务**
   - 设置合理的超时
   - 使用Celery Beat处理定时任务

---

## 🔮 后续改进

### 短期（本周）

1. ✅ 应用Celery到导出功能
   - [ ] PDF导出任务
   - [ ] 图片批量导出

2. ✅ 添加更多任务类型
   - [ ] 批量生成绘本
   - [ ] 定时清理任务

### 中期（本月）

1. **Celery Beat定时任务**
   - 每日清理旧草稿
   - 统计任务执行情况

2. **任务优先级队列**
   - 高优先级：VIP用户
   - 低优先级：批量操作

3. **任务链和工作流**
   - 生成→审核→发布
   - 串行和并行任务

### 长期（季度）

1. **分布式Celery**
   - 多台服务器部署
   - 负载均衡

2. **监控告警**
   - 任务失败告警
   - Worker异常告警

3. **性能优化**
   - 任务结果缓存
   - Worker池优化

---

## 📞 故障排查

### 问题1: Worker启动失败

**症状**:
```
Error: Unable to connect to Redis
```

**解决**:
1. 检查Redis是否启动: `redis-cli ping`
2. 检查REDIS_URL配置
3. 检查防火墙设置

### 问题2: 任务一直PENDING

**可能原因**:
1. Worker未启动
2. 任务名称不匹配
3. Worker未注册任务

**解决**:
```bash
# 查看worker状态
celery -A app.core.celery_app inspect active

# 查看已注册任务
celery -A app.core.celery_app inspect registered
```

### 问题3: 任务执行超时

**症状**: 任务在55分钟后失败

**原因**: 软超时设置（task_soft_time_limit）

**解决**:
```python
# 在celery_app.py中调整超时
task_soft_time_limit=5400,  # 90分钟
task_time_limit=6000,        # 100分钟
```

---

## 🔗 相关资源

- [Celery官方文档](http://docs.celeryproject.org/)
- [Celery最佳实践](https://docs.celeryproject.org/en/stable/userguide/optimizing.html)
- [Flower监控工具](https://flower.readthedocs.io/)
- [Redis文档](https://redis.io/docs/)

---

## 📊 完成状态

| 任务 | 状态 |
|------|------|
| 配置Celery应用 | ✅ 完成 |
| 实现异步任务 | ✅ 完成 |
| 改造API端点 | ✅ 完成 |
| 任务状态API | ✅ 完成 |
| Worker启动脚本 | ✅ 完成 |
| 编写文档 | ✅ 完成 |

**整体进度**: 6/6 (100%)

---

**实施完成时间**: 2026-01-08
**实施者**: Claude Code
**优化类型**: Celery任务队列
**影响范围**: 长时间运行任务
**测试状态**: ✅ 通过
**部署要求**: 需要Redis和Celery Worker
