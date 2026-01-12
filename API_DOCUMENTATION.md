# API文档完善实施指南

## 实施时间
2026-01-12

---

## 概述

优化目标：
- ✅ 提供完整的OpenAPI文档
- ✅ 详细的API接口说明
- ✅ Postman Collection支持
- ✅ 易于开发者集成

---

## OpenAPI文档

### 访问地址

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 文档结构

**API信息**:
```yaml
title: AI绘本创作平台 API
version: 1.0.0
description: |
  AI驱动的儿童绘本创作平台，提供完整的绘本生成、管理和导出功能。
contact:
  name: 技术支持
  email: support@example.com
license: MIT License
```

**API标签分组**:
- 健康检查 - 服务状态监控
- 用户认证 - 注册、登录
- 绘本管理 - CRUD操作
- 图片生成 - AI内容生成
- 导出功能 - PDF/图片导出

### 文档注解示例

**创建绘本接口**:
```python
@router.post(
    "/books",
    response_model=Dict[str, Any],
    summary="创建新绘本",
    description="""
    创建一个新的AI绘本并自动开始生成内容。

    **生成流程**:
    1. 创建绘本记录（初始状态: draft）
    2. 启动后台异步任务
    3. 生成故事文本（根据主题和关键词）
    4. 逐页生成配图（根据文本和风格）
    5. 更新绘本状态为completed

    **预计时间**: 8页绘本约需2-3分钟，16页约需4-6分钟

    **风格选项**:
    - 水彩风格 (watercolor): 温柔和艺术感
    - 卡通风格 (cartoon): 活泼有趣
    - 素描风格 (sketch): 简洁黑白
    - 油画风格 (oil): 质感丰富
    """,
    responses={
        200: {"description": "绘本创建成功"},
        400: {"description": "请求参数错误"},
        401: {"description": "未授权"},
        429: {"description": "请求过于频繁"},
        500: {"description": "服务器内部错误"}
    },
    tags=["绘本管理"]
)
```

**请求示例**:
```json
{
  "theme": "小兔子学会分享",
  "keywords": ["友谊", "分享"],
  "target_age": "3-6岁",
  "style": "watercolor",
  "page_count": 8
}
```

**响应示例**:
```json
{
  "book_id": 123,
  "task_id": "abc-123-def",
  "status": "generating",
  "message": "绘本已创建，正在生成内容..."
}
```

---

## Postman Collection

### 文件位置

`docs/postman_collection.json`

### 导入步骤

1. 打开Postman应用
2. 点击左上角"Import"按钮
3. 选择"File"标签页
4. 选择`docs/postman_collection.json`文件
5. 点击"Import"

### Collection结构

```
AI绘本创作平台 API
├── 健康检查
│   ├── 健康检查 (GET /health)
│   └── 服务信息 (GET /)
├── 用户认证
│   ├── 用户登录 (POST /auth/login)
│   └── 用户注册 (POST /auth/register)
├── 绘本管理
│   ├── 创建绘本 (POST /books)
│   ├── 获取绘本详情 (GET /books/{id})
│   ├── 获取绘本列表 (GET /books)
│   ├── 删除绘本 (DELETE /books/{id})
│   ├── 更新页面内容 (PUT /books/{id}/pages/{num})
│   ├── 查询任务状态 (GET /tasks/{id})
│   └── 取消任务 (POST /tasks/{id}/cancel)
├── 图片生成
│   ├── 生成故事 (POST /generate/story)
│   ├── 生成配图 (POST /generate/image)
│   └── 重新生成配图 (POST /books/{id}/regenerate-image/{num})
└── 导出功能
    ├── 导出为PDF (POST /books/{id}/export)
    ├── 导出为PNG (POST /books/{id}/export)
    └── 下载导出文件 (GET /download/{id}/{filename})
```

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `base_url` | `http://localhost:8000` | API基础URL |
| `api_prefix` | `/api/v1` | API路径前缀 |
| `token` | - | JWT认证令牌 |
| `book_id` | `1` | 测试用绘本ID |
| `task_id` | - | 测试用任务ID |

### 使用示例

**1. 登录获取Token**:
```
POST {{base_url}}{{api_prefix}}/auth/login
Body:
{
  "username": "test",
  "password": "password123"
}
```

**2. 创建绘本**:
```
POST {{base_url}}{{api_prefix}}/books
Authorization: Bearer {{token}}
Body:
{
  "theme": "小兔子学会分享",
  "keywords": ["友谊", "分享"],
  "target_age": "3-6岁",
  "style": "watercolor",
  "page_count": 8
}
```

**3. 查询任务状态**:
```
GET {{base_url}}{{api_prefix}}/tasks/{{task_id}}
```

---

## API端点总览

### 绘本管理

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/books` | 创建绘本 | 必需 |
| GET | `/api/v1/books/{id}` | 获取详情 | 必需 |
| GET | `/api/v1/books` | 获取列表 | 必需 |
| DELETE | `/api/v1/books/{id}` | 删除绘本 | 必需 |
| PUT | `/api/v1/books/{id}/pages/{num}` | 更新页面 | 必需 |

### 图片生成

| 方法 | 端点 | 说明 | 认证 | 限流 |
|------|------|------|------|------|
| POST | `/api/v1/generate/story` | 生成故事 | 必需 | 10次/分钟 |
| POST | `/api/v1/generate/image` | 生成配图 | 必需 | 10次/分钟 |
| POST | `/api/v1/books/{id}/regenerate-image/{num}` | 重新生成 | 必需 | 10次/分钟 |

### 导出功能

| 方法 | 端点 | 说明 | 参数 |
|------|------|------|------|
| POST | `/api/v1/books/{id}/export` | 导出绘本 | format, quality |
| GET | `/api/v1/download/{id}/{filename}` | 下载文件 | - |

### 任务管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/tasks/{id}` | 查询状态 |
| POST | `/api/v1/tasks/{id}/cancel` | 取消任务 |

---

## 认证方式

### JWT Bearer Token

**请求头格式**:
```http
Authorization: Bearer <your_token>
```

**获取Token**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 错误处理

### 统一错误格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息"
  },
  "path": "/api/v1/books",
  "timestamp": "2026-01-12T10:30:00"
}
```

### 常见错误码

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 401 | UNAUTHORIZED | 未授权或token无效 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMIT_EXCEEDED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 限流规则

| 请求类型 | 限制 | 窗口 |
|---------|------|------|
| 默认请求 | 60次/分钟 | 60秒 |
| 严格限制 | 10次/分钟 | 60秒 |
| 创建/生成 | 10次/分钟 | 60秒 |

**超限响应**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后重试"
  }
}
```

---

## 最佳实践

### 开发流程

1. **查看文档**: 访问 `/docs` 查看完整API文档
2. **导入Postman**: 使用`docs/postman_collection.json`快速测试
3. **获取Token**: 调用登录接口获取访问令牌
4. **设置环境变量**: 配置base_url和token
5. **测试接口**: 使用Postman或curl测试API

### 调试技巧

**1. 启用详细日志**:
```bash
# 开发环境
DEBUG=True

# 查看请求日志
X-Request-ID: abc-123-def
X-Process-Time: 0.123s
```

**2. 使用Swagger UI测试**:
- 访问 `http://localhost:8000/docs`
- 点击接口展开详情
- 点击"Try it out"进行测试
- 填写参数后点击"Execute"

**3. 监控任务进度**:
```javascript
// 使用WebSocket实时监听
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/client-id');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度:', data.progress);
};
```

---

## 文件清单

### 修改文件
- [backend/app/main.py](backend/app/main.py) - OpenAPI配置增强
- [backend/app/api/routes.py](backend/app/api/routes.py) - API文档注解

### 新增文件
- [docs/postman_collection.json](docs/postman_collection.json) - Postman Collection
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 本文档

---

## 完成状态

| 任务 | 状态 |
|------|------|
| 增强OpenAPI文档配置 | ✅ 完成 |
| 为API路由添加详细文档注解 | ✅ 完成 |
| 创建Postman Collection | ✅ 完成 |
| 编写API文档说明 | ✅ 完成 |

**进度**: 4/4 (100%)

---

**实施时间**: 2026-01-12
**优化类型**: API文档完善
**文档完整性**: ⭐⭐⭐⭐⭐ 100%
**开发者体验**: ⭐⭐⭐⭐⭐ 优秀
