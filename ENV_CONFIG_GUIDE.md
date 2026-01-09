# 环境变量配置指南

## 实施时间
2026-01-09

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [配置详解](#配置详解)
- [验证机制](#验证机制)
- [安全最佳实践](#安全最佳实践)
- [故障排查](#故障排查)

---

## 概述

### 什么是环境变量？

环境变量是在操作系统级别存储的动态值，应用程序可以在运行时读取这些值。它们用于：

- **配置管理**: 分离配置与代码
- **安全性**: 避免将敏感信息硬编码
- **灵活性**: 不同环境使用不同配置
- **可移植性**: 方便部署到不同环境

### 本项目的环境变量验证

AI绘本平台实现了**全面的环境变量验证系统**，包括：

- ✅ 启动时自动验证
- ✅ 分层验证（必需/可选）
- ✅ 连接测试
- ✅ 友好的错误提示
- ✅ 配置摘要显示

---

## 快速开始

### 1. 创建配置文件

```bash
# 进入后端目录
cd backend

# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# Linux/Mac: nano .env 或 vim .env
```

### 2. 填写必需配置

编辑 `.env` 文件，至少配置以下变量：

```env
# 文本生成API密钥
TEXT_API_KEY=sk-your-actual-api-key-here

# 图像生成API密钥
IMAGE_API_KEY=sk-your-actual-api-key-here

# 数据库（使用默认SQLite即可）
DATABASE_URL=sqlite:///./picturebook.db

# 运行环境
DEBUG=true
```

### 3. 启动服务

```bash
# 开发环境
python -m uvicorn app.main:app --reload

# 生产环境（先设置DEBUG=false）
DEBUG=false python -m uvicorn app.main:app
```

### 4. 验证输出

启动时你会看到类似的输出：

```
============================================================
AI绘本创作平台 - 后端服务启动
启动时间: 2026-01-09 10:30:00
============================================================
🔍 验证环境配置...
  📋 验证必需的环境变量...
  🌐 验证URL格式...
  🔢 验证数值范围...
  📁 验证路径配置...
  🔐 验证JWT配置...
  🔗 测试外部服务连接...
    🗄️  测试数据库连接...
    ✅ 数据库连接成功
    🤖 测试AI服务API连接...
    ✅ 文本生成API 连接成功
    ✅ 图像生成API 连接成功

✅ 配置验证通过！

📊 配置摘要:
  环境: 开发环境
  数据库: sqlite:///./picturebook.db
  文本API: https://api.openai.com/v1
  图像API: https://api.openai.com/v1

============================================================
✅ 服务启动成功，准备接收请求
============================================================
```

---

## 配置详解

### 必需配置

#### 1. AI服务密钥

**TEXT_API_KEY** (文本生成)
```env
# 必需，用于生成绘本故事
TEXT_API_KEY=sk-proj-xxxxxxxxxxxxx

# 或使用兼容OpenAI的服务
TEXT_API_KEY=your-api-key
TEXT_BASE_URL=https://your-api-endpoint.com/v1
```

**IMAGE_API_KEY** (图像生成)
```env
# 必需，用于生成绘本插图
IMAGE_API_KEY=sk-proj-xxxxxxxxxxxxx

# 或使用兼容OpenAI的服务
IMAGE_API_KEY=your-api-key
IMAGE_BASE_URL=https://your-api-endpoint.com/v1
```

**向后兼容**（旧版本支持）
```env
# 如果未设置TEXT_API_KEY和IMAGE_API_KEY，
# 系统将使用OPENAI_API_KEY作为默认值
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### 2. 数据库配置

**开发环境**（SQLite）
```env
# 默认配置，开箱即用
DATABASE_URL=sqlite:///./picturebook.db
```

**生产环境**（PostgreSQL）
```env
# PostgreSQL配置
DATABASE_URL=postgresql://username:password@localhost:5432/picturebook

# 连接池配置
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_ECHO=false
```

### 可选配置

#### 1. 应用基础配置

```env
# 应用名称
APP_NAME=AI绘本创作平台

# 运行环境
DEBUG=true          # 开发环境
DEBUG=false         # 生产环境

# API前缀
API_PREFIX=/api/v1
```

#### 2. JWT认证配置

```env
# JWT密钥（生产环境必须设置）
JWT_SECRET_KEY=your-secret-key-min-32-characters

# JWT过期时间（秒）
JWT_EXPIRATION_SECONDS=604800  # 7天
```

**生成安全的JWT密钥**:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"

# OpenSSL
openssl rand -base64 32
```

#### 3. CORS跨域配置

```env
# 开发环境
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# 生产环境（限制为实际域名）
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 4. 存储配置

```env
# 上传文件目录
UPLOAD_DIR=./uploads

# 输出文件目录
OUTPUT_DIR=./outputs
```

#### 5. Redis配置（可选）

```env
# 用于任务队列和缓存
REDIS_URL=redis://localhost:6379/0
```

#### 6. API调用配置

```env
# 请求超时时间（秒）
API_TIMEOUT=120

# 最大重试次数
API_MAX_RETRIES=3

# 重试延迟（秒）
API_RETRY_DELAY=2

# 备用API地址（可选）
API_BACKUP_BASE_URL=https://backup-api.example.com/v1

# 是否启用备用地址
API_ENABLE_FALLBACK=true
```

---

## 验证机制

### 自动验证层级

系统会在启动时执行以下验证：

#### 1. 基础验证

✅ **必需环境变量检查**
```python
# 检查必需变量是否存在
TEXT_API_KEY: ✓
IMAGE_API_KEY: ✓
DATABASE_URL: ✓
```

#### 2. 格式验证

✅ **URL格式验证**
```python
# 验证URL格式是否正确
DATABASE_URL: sqlite:///./picturebook.db ✓
TEXT_BASE_URL: https://api.openai.com/v1 ✓
IMAGE_BASE_URL: https://api.openai.com/v1 ✓
REDIS_URL: redis://localhost:6379/0 ✓
```

#### 3. 数值范围验证

✅ **数值参数验证**
```python
# 检查数值是否在合理范围
API_TIMEOUT=120: [1, 600] ✓
API_MAX_RETRIES=3: [0, 10] ✓
DB_POOL_SIZE=5: [1, 100] ✓
```

#### 4. 安全性验证

✅ **JWT密钥强度检查**
```python
# 检查JWT密钥强度
JWT_SECRET_KEY:
  - 长度: 43字符 ✓
  - 弱密钥检测: 通过 ✓
```

#### 5. 连接测试

✅ **外部服务连接测试**
```python
# 测试数据库连接
Database: ✓

# 测试文本API
Text API: ✓ (200ms)

# 测试图像API
Image API: ✓ (180ms)

# 测试Redis（可选）
Redis: ✓
```

### 验证失败处理

#### 开发环境

```bash
# 开发环境会给出警告，但允许继续启动
⚠️  开发环境检测到以下环境变量未设置: TEXT_API_KEY
⚠️  开发环境：配置验证失败但继续启动
```

#### 生产环境

```bash
# 生产环境会严格验证，失败则退出
❌ 配置验证失败 - 缺少必需的环境变量:
  ❌ TEXT_API_KEY 未设置

💡 解决方案:
  1. 检查 .env 文件是否存在
  2. 参考 .env.example 文件配置所有必需的环境变量
  3. 确保所有必需的服务正在运行

# 系统退出，状态码: 1
SystemExit: 1
```

---

## 安全最佳实践

### ✅ 推荐做法

#### 1. 永远不要提交 .env 文件

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

#### 2. 使用强随机密钥

```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 输出: 8KXz7xMqN9vR2tY5wL6pH8yJ3kN9mP2xQ7vR4tY6wL9
```

#### 3. 不同环境使用不同配置

```bash
# 开发环境
.env.development

# 生产环境
.env.production

# 测试环境
.env.test
```

#### 4. 使用密钥管理服务

生产环境建议使用：
- **AWS Secrets Manager**
- **Azure Key Vault**
- **Google Secret Manager**
- **HashiCorp Vault**

#### 5. 限制API权限

- 为API密钥设置最小权限
- 定期轮换密钥
- 监控API使用情况

### ❌ 避免的做法

#### 1. 不要硬编码密钥

```python
# ❌ 不好
API_KEY = "sk-proj-1234567890"

# ✅ 好
API_KEY = os.getenv("API_KEY")
```

#### 2. 不要在日志中输出密钥

```python
# ❌ 不好
logger.info(f"Using API key: {API_KEY}")

# ✅ 好
logger.info(f"Using API key: {API_KEY[:10]}...")
```

#### 3. 不要使用弱密钥

```env
# ❌ 不好
JWT_SECRET_KEY=secret
JWT_SECRET_KEY=password
JWT_SECRET_KEY=123456

# ✅ 好
JWT_SECRET_KEY=8KXz7xMqN9vR2tY5wL6pH8yJ3kN9mP2xQ7vR4tY6wL9
```

---

## 故障排查

### 问题1: 启动时提示配置验证失败

**症状**:
```
❌ 配置验证失败 - 缺少必需的环境变量:
  ❌ TEXT_API_KEY 未设置
```

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认变量名称拼写正确
3. 检查是否有额外空格
4. 确保没有引号包裹值

### 问题2: API连接测试失败

**症状**:
```
❌ 文本生成API连接失败
```

**解决方案**:
1. 检查API密钥是否正确
2. 验证 `TEXT_BASE_URL` 是否可访问
3. 检查网络连接和防火墙
4. 确认API服务状态正常

### 问题3: 数据库连接失败

**症状**:
```
❌ 数据库连接失败: access denied
```

**解决方案**:
1. 检查数据库是否运行
2. 验证 `DATABASE_URL` 格式
3. 确认用户名和密码正确
4. 检查数据库权限

### 问题4: 跨域问题

**症状**:
前端无法访问后端API，浏览器CORS错误

**解决方案**:
```env
# 检查 ALLOWED_ORIGINS 配置
ALLOWED_ORIGINS=http://localhost:5173

# 确保前端地址包含在内
```

### 问题5: 环境变量未生效

**症状**:
修改了 `.env` 文件但配置没有变化

**解决方案**:
1. 重启应用（环境变量只在启动时读取）
2. 检查文件名是否为 `.env`（不是 `.env.txt`）
3. 确保文件在正确位置（backend/.env）
4. 检查文件编码（应为UTF-8）

---

## 验证命令

### 手动验证配置

```python
# backend/verify_config.py
import asyncio
from app.config import settings

async def main():
    print("🔍 验证环境配置...\n")

    # 执行验证
    passed = await settings.validate(
        skip_connection_tests=False  # 包含连接测试
    )

    if passed:
        print("\n✅ 所有验证通过！")
    else:
        print("\n❌ 验证失败，请检查配置")

if __name__ == "__main__":
    asyncio.run(main())
```

运行验证：
```bash
cd backend
python verify_config.py
```

---

## 配置检查清单

### 开发环境启动前

- [ ] `.env` 文件已创建
- [ ] `TEXT_API_KEY` 已配置
- [ ] `IMAGE_API_KEY` 已配置
- [ ] `DATABASE_URL` 已配置
- [ ] `DEBUG=true`
- [ ] `ALLOWED_ORIGINS` 包含前端地址

### 生产环境部署前

- [ ] 所有开发环境配置已移除
- [ ] `DEBUG=false`
- [ ] `JWT_SECRET_KEY` 已设置为强密钥
- [ ] 数据库使用PostgreSQL
- [ ] `ALLOWED_ORIGINS` 限制为实际域名
- [ ] 日志配置正确
- [ ] HTTPS证书已配置
- [ ] API密钥使用生产环境专用密钥
- [ ] 备用API已配置
- [ ] 监控和告警已配置

---

## 进阶配置

### 多环境配置

```bash
# 目录结构
backend/
├── .env                    # 默认配置（不提交）
├── .env.example           # 示例配置（提交）
├── .env.development       # 开发环境（可选）
├── .env.production        # 生产环境（可选）
└── .env.test              # 测试环境（可选）
```

加载不同环境配置：
```python
import os
from pathlib import Path

# 获取当前环境
env = os.getenv("ENVIRONMENT", "development")

# 加载对应的 .env 文件
env_file = Path(f".env.{env}")
if env_file.exists():
    # pydantic-settings 会自动加载
    pass
```

### 动态配置

```python
# 从环境变量读取环境
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 根据环境设置不同的配置
if ENVIRONMENT == "production":
    DEBUG = False
    LOG_LEVEL = "WARNING"
    DATABASE_URL = "postgresql://..."
else:
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATABASE_URL = "sqlite:///./dev.db"
```

---

## 📚 相关资源

- [Python-dotenv文档](https://pypi.org/project/python-dotenv/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [环境变量最佳实践](https://12factor.net/config)

---

**实施完成时间**: 2026-01-09
**实施者**: Claude Code
**优化类型**: 环境变量验证
**影响范围**: 后端配置系统
**安全提升**: ⭐⭐⭐⭐⭐ 显著提升
**开发体验**: ⭐⭐⭐⭐⭐ 友好度大幅提升
