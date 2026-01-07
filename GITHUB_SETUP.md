# 📤 GitHub 推送指南

## 快速开始

### 方法 1: 使用 Python 向导（推荐）

```bash
python setup_github.py
```

按照向导提示操作即可。

### 方法 2: 使用 Shell 脚本

```bash
bash setup_github.sh <YOUR_GITHUB_REPO_URL>
```

### 方法 3: 手动操作

#### 步骤 1: 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息:
   - Repository name: `ai-picture-book`
   - Description: `AI-powered children's picture book creation platform`
   - ⚠️ **不要勾选** "Add a README file"
   - 可选择添加 .gitignore（但项目已有）
   - 可选择 License（推荐 MIT）

3. 点击 "Create repository"

#### 步骤 2: 推送代码到 GitHub

**使用 HTTPS:**
```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-picture-book.git
git branch -M master
git push -u origin master
```

**使用 SSH:**
```bash
git remote add origin git@github.com:YOUR_USERNAME/ai-picture-book.git
git branch -M master
git push -u origin master
```

## 身份验证说明

### HTTPS 方式

需要使用 **Personal Access Token** (密码已弃用):

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置权限:
   - ✅ repo (完整仓库访问权限)
   - ✅ workflow (如果需要 GitHub Actions)
4. 生成并复制 token
5. 推送时输入用户名和 token:
   - Username: 你的 GitHub 用户名
   - Password: 粘贴 token (不是密码)

### SSH 方式（推荐）

需要配置 SSH 密钥:

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 启动 ssh-agent
eval "$(ssh-agent -s)"

# 添加密钥
ssh-add ~/.ssh/id_ed25519

# 复制公钥
cat ~/.ssh/id_ed25519.pub
```

1. 复制输出的公钥
2. 访问 https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥并添加

## 推送后检查清单

- [ ] 代码已成功推送到 GitHub
- [ ] README.md 显示正确
- [ ] 检查仓库的文件列表
- [ ] 编辑仓库描述和标签
- [ ] 添加项目网站链接（如果有）
- [ ] 设置仓库为 Public 或 Private

## 仓库美化建议

### 1. 更新 README.md

添加以下内容:
- 项目截图/演示 GIF
- 功能特性列表
- 安装和使用说明
- 技术栈图标
- 许可证徽章

### 2. 添加 GitHub Topics

在仓库设置中添加标签:
```
ai, picture-book, fastapi, react, python, typescript,
children, education, story-generation, image-generation
```

### 3. 设置仓库描述

```
AI-powered children's picture book creation platform.
Generate stories and illustrations automatically using AI.
```

### 4. 启用 GitHub Issues

用于 bug 追踪和功能请求。

### 5. 添加 Contributing Guidelines

创建 `CONTRIBUTING.md` 文件说明贡献规范。

## 常见问题

### Q: 推送时提示 "Permission denied"
**A:** 检查身份验证方式，HTTPS 需要使用 token，SSH 需要配置密钥。

### Q: 提示 "remote already exists"
**A:** 使用 `git remote set-url origin <URL>` 更新远程仓库地址。

### Q: 推送后看不到某些文件
**A:** 检查 `.gitignore` 文件，可能被忽略了。

### Q: 如何删除 Git 历史
**A:**
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit"
```

## 项目仓库信息

- **本地分支**: master
- **远程仓库**: origin (待添加)
- **提交数**: 1 (初始提交)
- **文件数**: 34
- **代码行数**: ~6000

## 下一步

推送成功后，您可以:

1. ✨ 在 GitHub 上编辑 README.md
2. 🎨 添加项目截图和演示
3. 📝 编写详细的文档
4. 🏷️ 设置 release 和版本标签
5. 🚀 配置 GitHub Actions (CI/CD)
6. 🌐 启用 GitHub Pages (部署前端)

## 需要帮助?

- GitHub 官方文档: https://docs.github.com
- Git 官方文档: https://git-scm.com/docs
- 推送向导: `python setup_github.py`
