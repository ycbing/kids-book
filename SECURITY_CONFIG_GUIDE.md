# 安全配置指南

## ⚠️ 重要：API密钥已从代码中移除

为了确保项目安全，我们已经完成了以下安全改进：

### ✅ 已完成的安全修复

1. **移除硬编码密钥**
   - 从 `backend/app/config.py` 中移除了硬编码的API密钥
   - 所有敏感信息现在必须通过环境变量配置

2. **添加配置验证**
   - 生产环境启动时会自动验证必需的环境变量
   - 开发环境会给出友好提示

3. **环境变量隔离**
   - `.env` 文件已在 `.gitignore` 中，不会被提交到Git
   - 提供 `.env.example` 作为配置模板

---

## 📝 配置步骤

### 第一步：配置环境变量

编辑 `backend/.env` 文件，填入你的实际API密钥：

```bash
# 进入后端目录
cd backend

# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

### 第二步：填入必需的配置

在 `backend/.env` 中，至少需要配置以下内容：

```env
# 文本生成服务 - 必需
TEXT_API_KEY=sk-your-actual-api-key-here
TEXT_BASE_URL=https://api.siliconflow.cn/v1
TEXT_MODEL=THUDM/GLM-4.1V-9B-Thinking

# 图像生成服务 - 必需
IMAGE_API_KEY=sk-your-actual-api-key-here
IMAGE_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_MODEL=Qwen/Qwen-Image
IMAGE_SIZE=1024x1024
```

### 第三步：验证配置

启动后端服务，系统会自动验证配置：

```bash
# 开发环境（DEBUG=true）
# 会给出警告，但不会阻止启动
python -m app.main

# 生产环境（DEBUG=false）
# 如果配置缺失，会阻止启动并显示错误
DEBUG=false python -m app.main
```

---

## 🔒 安全最佳实践

### 1. 永远不要提交密钥到Git

确保以下文件和模式在 `.gitignore` 中：

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# 但保留示例文件
!.env.example
```

### 2. 使用不同的密钥

- **开发环境**：使用测试密钥，有使用限额
- **生产环境**：使用独立的生产密钥
- **定期轮换**：每3-6个月更换密钥

### 3. 环境隔离

```bash
# 开发环境
backend/.env.dev    # 开发配置
backend/.env.prod   # 生产配置（不要提交）

# 启动时指定环境
python -m app.main --env prod
```

### 4. 密钥权限管理

- 为不同环境使用不同的API密钥
- 设置密钥的使用限额和预算告警
- 定期检查API使用日志
- 密钥泄露后立即撤销

---

## 🚨 如果密钥已泄露

如果你的密钥已经被提交到Git仓库：

### 1. 立即撤销密钥
- 登录API服务商控制台
- 撤销已泄露的密钥
- 生成新的密钥

### 2. 清理Git历史（可选）

```bash
# 使用 git-filter-repo 清理历史
pip install git-filter-repo

# 从所有历史中移除密钥
git filter-repo --invert-paths --path backend/.env

# 强制推送（谨慎使用！）
git push origin --force --all
```

### 3. 通知团队成员

- 告知所有开发者密钥已泄露
- 要求更新本地配置
- 更新部署环境中的密钥

---

## 🔍 验证安全配置

运行以下命令检查是否有敏感信息泄露：

```bash
# 检查代码中是否包含API密钥
grep -r "sk-" --include="*.py" --exclude-dir=.git .

# 检查是否有.env文件被跟踪
git ls-files | grep "\.env"

# 应该返回空，如果返回文件名说明.env被跟踪了
```

---

## 📋 环境变量参考

### 必需配置

| 变量名 | 说明 | 示例值 | 必需 |
|--------|------|--------|------|
| `TEXT_API_KEY` | 文本生成API密钥 | `sk-xxxxx` | ✅ |
| `IMAGE_API_KEY` | 图像生成API密钥 | `sk-xxxxx` | ✅ |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TEXT_BASE_URL` | 文本API地址 | `https://api.openai.com/v1` |
| `TEXT_MODEL` | 文本生成模型 | `gpt-3.5-turbo` |
| `IMAGE_BASE_URL` | 图像API地址 | `https://api.openai.com/v1` |
| `IMAGE_MODEL` | 图像生成模型 | `dall-e-3` |
| `IMAGE_SIZE` | 图像尺寸 | `1024x1024` |
| `API_TIMEOUT` | 请求超时(秒) | `120` |
| `API_MAX_RETRIES` | 最大重试次数 | `3` |
| `DEBUG` | 调试模式 | `true` |

---

## 🛠️ 常见问题

### Q: 开发环境启动时报错缺少API密钥

**A**: 在 `backend/.env` 中配置密钥即可。如果只是测试，可以先设置 `DEBUG=true`，系统会给出警告但不会阻止启动。

### Q: 生产环境如何配置密钥？

**A**: 推荐使用环境变量或密钥管理服务：

```bash
# 方法1：直接设置环境变量
export TEXT_API_KEY="sk-xxxxx"
export IMAGE_API_KEY="sk-xxxxx"

# 方法2：使用 systemd service
# /etc/systemd/system/picturebook.service
Environment="TEXT_API_KEY=sk-xxxxx"
Environment="IMAGE_API_KEY=sk-xxxxx"

# 方法3：使用 Docker secrets
docker-compose.yml 中配置：
services:
  backend:
    secrets:
      - api_keys
secrets:
  api_keys:
    file: ./secrets/api_keys.txt
```

### Q: 如何检查当前配置？

**A**: 启动服务后，查看日志输出：

```bash
python -m app.main
# 日志会显示：
# ✅ 配置验证通过  或
# ⚠️  开发环境检测到以下环境变量未设置: TEXT_API_KEY, IMAGE_API_KEY
```

---

## 📚 相关资源

- [优化建议文档](./OPTIMIZATION_RECOMMENDATIONS.md)
- [环境变量示例](./backend/.env.example)
- [OWASP密钥管理最佳实践](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)

---

**最后更新**: 2026-01-08
**维护者**: 开发团队
