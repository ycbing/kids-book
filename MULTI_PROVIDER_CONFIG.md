# 多服务商配置说明

## 更新说明

现在支持为**文本生成**和**图像生成**使用不同的AI服务商，每个服务可以配置独立的：
- API密钥 (API Key)
- 服务地址 (Base URL)
- 模型名称 (Model)

## 配置方式

### 方式一：分别配置（推荐）

在 `.env` 文件中配置不同的服务商：

```bash
# ==================== 文本生成服务 ====================
TEXT_API_KEY=sk-text-provider-key
TEXT_BASE_URL=https://text-api.example.com/v1
TEXT_MODEL=gpt-3.5-turbo

# ==================== 图像生成服务 ====================
IMAGE_API_KEY=sk-image-provider-key
IMAGE_BASE_URL=https://image-api.example.com/v1
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024
```

### 方式二：使用统一服务商

如果两个服务使用同一个服务商，只需配置一次：

```bash
# 只配置统一的API密钥和地址
OPENAI_API_KEY=sk-unified-key
OPENAI_BASE_URL=https://api.example.com/v1

# 模型仍然分开配置
TEXT_MODEL=gpt-3.5-turbo
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024
```

### 方式三：混合配置

文本用一个服务商，图像用另一个：

```bash
# 文本使用服务商A
TEXT_API_KEY=sk-provider-a-key
TEXT_BASE_URL=https://provider-a.com/v1
TEXT_MODEL=claude-3-sonnet

# 图像使用服务商B（使用统一的OPENAI_API_KEY）
IMAGE_API_KEY=sk-provider-b-key
IMAGE_BASE_URL=https://provider-b.com/v1
IMAGE_MODEL=stable-diffusion-xl
```

## 常见配置示例

### 示例1: SiliconFlow 全家桶

```bash
# SiliconFlow 提供文本和图像服务
TEXT_API_KEY=sk-siliconflow-key
TEXT_BASE_URL=https://api.siliconflow.cn/v1
TEXT_MODEL=Qwen/Qwen2-7B-Instruct

IMAGE_API_KEY=sk-siliconflow-key
IMAGE_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
IMAGE_SIZE=1024x1024
```

### 示例2: OpenAI + 第三方图像

```bash
# 文本使用 OpenAI
TEXT_API_KEY=sk-openai-key
TEXT_BASE_URL=https://api.openai.com/v1
TEXT_MODEL=gpt-4

# 图像使用第三方中转
IMAGE_API_KEY=sk-thirdparty-key
IMAGE_BASE_URL=https://third-party.com/v1
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024
```

### 示例3: 国内服务商组合

```bash
# 文本使用通义千问
TEXT_API_KEY=sk-qwen-key
TEXT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_MODEL=qwen-turbo

# 图像使用硅基流动
IMAGE_API_KEY=sk-siliconflow-key
IMAGE_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_MODEL=stabilityai/stable-diffusion-3
IMAGE_SIZE=1024x1024
```

## 配置优先级

系统按以下优先级查找配置：

1. **新配置**（优先使用）:
   - `TEXT_API_KEY` + `TEXT_BASE_URL` + `TEXT_MODEL`
   - `IMAGE_API_KEY` + `IMAGE_BASE_URL` + `IMAGE_MODEL`

2. **旧配置**（向后兼容）:
   - `OPENAI_API_KEY` + `OPENAI_BASE_URL`

3. **默认值**（都没有时）:
   - Base URL: `https://api.openai.com/v1`

## 验证配置

启动后端服务时，查看日志输出：

```
AI服务初始化完成
文本API地址: https://your-text-api.com/v1
文本模型: your-text-model
图像API地址: https://your-image-api.com/v1
图像模型: your-image-model
超时设置: 120秒
最大重试: 3次
```

确认配置的地址和模型正确。

## 迁移指南

如果你已经在使用旧配置（`OPENAI_API_KEY`），不需要立即修改：

1. **现有配置继续工作** - 向后兼容保证
2. **逐步迁移** - 可以先配置 `TEXT_*`，保留 `OPENAI_*`
3. **测试验证** - 确认新配置工作后再删除旧配置

## 故障排查

### 问题：文本生成正常，但图像生成失败

**原因**：图像API配置错误或密钥无效

**解决**：
1. 检查 `IMAGE_API_KEY` 和 `IMAGE_BASE_URL`
2. 确认图像服务商的账户余额
3. 查看后端日志中的详细错误信息

### 问题：所有请求都失败

**原因**：配置未生效或环境变量未加载

**解决**：
1. 确认 `.env` 文件在 `backend/` 目录下
2. 重启后端服务
3. 检查环境变量是否正确设置

### 问题：想使用不同的模型但不知道配置什么

**参考**：
- 查看[模型配置指南](MODEL_CONFIG_GUIDE.md)
- 确认服务商支持的模型列表
- 测试模型是否可用

## 相关文件

- [backend/app/config.py](backend/app/config.py) - 配置定义
- [backend/app/services/ai_service.py](backend/app/services/ai_service.py) - AI服务实现
- [backend/.env.example](backend/.env.example) - 环境变量示例
