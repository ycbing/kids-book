# 🔄 第三方中转站API调用优化说明

## 功能特性

### 1. 自动重试机制
- ✅ 遇到网络错误自动重试（最多3次）
- ✅ 指数退避策略（2秒 → 4秒 → 8秒）
- ✅ 支持自定义重试次数和延迟

### 2. 超时控制
- ✅ 可配置的请求超时时间（默认120秒）
- ✅ 防止长时间挂起
- ✅ 适合第三方中转站的响应时间

### 3. 错误处理
- ✅ 智能错误识别和分类
- ✅ 友好的错误提示
- ✅ 详细的日志记录

### 4. 备用地址支持
- ✅ 主API失败时自动切换到备用地址
- ✅ 支持多个备用地址配置
- ✅ 自动健康检查

## 配置说明

### 1. 基础配置（config.py）

```python
# API调用配置
API_TIMEOUT: int = 120  # 超时时间（秒）
API_MAX_RETRIES: int = 3  # 最大重试次数
API_RETRY_DELAY: int = 2  # 重试延迟（秒）
API_BACKUP_BASE_URL: Optional[str] = None  # 备用API地址
API_ENABLE_FALLBACK: bool = True  # 是否启用备用地址
```

### 2. 环境变量配置（.env）

```bash
# API超时配置
API_TIMEOUT=120

# 重试配置
API_MAX_RETRIES=3
API_RETRY_DELAY=2

# 备用地址（可选）
API_BACKUP_BASE_URL=https://backup-api.example.com/v1
API_ENABLE_FALLBACK=true
```

## 重试策略

### 重试条件

以下情况会触发自动重试：

1. **网络连接错误**
   - ConnectionError
   - TimeoutError
   - APIConnectionError

2. **API服务错误**
   - 5xx 服务器错误
   - 429 Too Many Requests
   - 503 Service Unavailable

3. **临时性错误**
   - 网络波动
   - 服务暂时不可用
   - 第三方中转站限流

### 重试行为

```
第1次尝试 → 失败
等待 2 秒
第2次尝试 → 失败
等待 4 秒 (2 × 2)
第3次尝试 → 失败
等待 8 秒 (4 × 2)
第4次尝试 → 成功/失败
```

## 错误处理

### 错误类型映射

| 错误类型 | 用户提示 | 建议 |
|---------|---------|------|
| 超时错误 | API请求超时，请稍后重试 | 增加超时时间或检查网络 |
| 连接错误 | 无法连接到API服务器 | 检查网络和API地址 |
| 认证错误 | API密钥无效 | 检查API密钥配置 |
| 限流错误 | API请求频率超限 | 稍后再试或升级套餐 |
| 配额错误 | API配额已用完 | 检查账户余额 |

### 错误日志示例

```
❌ 第 1 次重试 generate_story...
❌ generate_story 失败 (尝试 1/4): APIConnectionError: Connection refused
⚠️  第 2 次重试 generate_story...
✅ 重试成功! (尝试次数: 2)
```

## 使用示例

### 1. 基础使用（自动重试）

```python
from app.services.ai_service import ai_service

# 自动重试已配置，直接调用即可
story = await ai_service.generate_story(request)
```

### 2. 自定义重试配置

```python
from app.services.retry_helper import retry_on_failure

@retry_on_failure(
    max_retries=5,  # 重试5次
    delay=1,  # 初始延迟1秒
    backoff_factor=1.5  # 退避因子1.5
)
async def my_api_call():
    # 您的API调用代码
    pass
```

### 3. 手动错误处理

```python
from app.services.ai_service import ai_service
from app.services.retry_helper import APICallError

try:
    story = await ai_service.generate_story(request)
except APICallError as e:
    # 处理特定错误
    if e.status_code == 429:
        # 限流错误
        await asyncio.sleep(60)
    elif e.status_code == 401:
        # 认证错误
        logger.error("API密钥错误")
    else:
        logger.error(f"API错误: {e}")
```

## 监控和调试

### 1. 查看重试日志

```
2026-01-07 16:33:45 - app.services.ai_service - INFO - 🎨 开始生成故事
2026-01-07 16:33:45 - app.services.ai_service - INFO - 📤 向AI发送请求...
2026-01-07 16:33:56 - app.services.ai_service - INFO - 📥 收到AI响应
2026-01-07 16:33:56 - app.services.ai_service - INFO - ✅ 故事生成成功!
```

### 2. 性能监控

- 每个请求会记录处理时间
- 重试次数会被记录
- 错误详情会被保存

### 3. 测试API连接

```python
from app.services.retry_helper import test_api_connection
from app.config import settings

# 测试主API地址
success = await test_api_connection(
    settings.OPENAI_BASE_URL,
    settings.OPENAI_API_KEY
)
```

## 最佳实践

### 1. 超时设置

```python
# 快速响应（文本生成）
API_TIMEOUT = 60

# 正常响应（图像生成）
API_TIMEOUT = 120

# 慢速响应（复杂任务）
API_TIMEOUT = 180
```

### 2. 重试策略

```python
# 关键任务（多次重试）
API_MAX_RETRIES = 5

# 普通任务（标准重试）
API_MAX_RETRIES = 3

# 快速失败（少重试）
API_MAX_RETRIES = 1
```

### 3. 延迟设置

```python
# 快速重试
API_RETRY_DELAY = 1

# 标准重试
API_RETRY_DELAY = 2

# 慢速重试（避免限流）
API_RETRY_DELAY = 5
```

## 故障排除

### 问题1: 频繁超时

**原因**: 第三方中转站响应慢

**解决方案**:
```bash
# 增加超时时间
API_TIMEOUT=180  # 增加到3分钟
```

### 问题2: 限流错误

**原因**: 请求频率过高

**解决方案**:
```bash
# 增加重试延迟
API_RETRY_DELAY=5

# 或减少并发请求
```

### 问题3: 认证失败

**原因**: API密钥错误或过期

**解决方案**:
```bash
# 检查API密钥
OPENAI_API_KEY=sk-your-correct-key

# 检查API地址
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

## 技术细节

### 重试装饰器实现

```python
@retry_on_failure(
    max_retries=3,
    delay=2,
    backoff_factor=2.0,
    exceptions=(openai.APIError, Exception)
)
```

**参数说明**:
- `max_retries`: 最大重试次数
- `delay`: 初始延迟时间
- `backoff_factor`: 退避因子
- `exceptions`: 需要重试的异常类型

### 日志级别

- `INFO`: 正常操作日志
- `WARNING`: 重试警告
- `ERROR`: 失败错误

## 更新日志

### v1.1 (2026-01-07)

- ✅ 添加自动重试机制
- ✅ 添加超时控制
- ✅ 添加错误分类处理
- ✅ 添加备用地址支持
- ✅ 优化日志输出
- ✅ 添加配置示例文件

## 相关文件

- `backend/app/config.py` - 配置文件
- `backend/app/services/ai_service.py` - AI服务（带重试）
- `backend/app/services/retry_helper.py` - 重试辅助函数
- `backend/.env.example` - 环境变量示例
