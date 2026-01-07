# 🚀 快速推送到 GitHub

## 最简单的方法

运行 Python 向导并按提示操作：

```bash
python setup_github.py
```

## 手动操作（3步）

### 1️⃣ 在 GitHub 创建仓库

访问: https://github.com/new

- Repository name: `ai-picture-book`
- ⚠️ **不要** 勾选 "Add a README file"
- 点击 "Create repository"

### 2️⃣ 复制仓库 URL

创建后会显示 URL，选择 HTTPS 或 SSH：
- HTTPS: `https://github.com/YOUR_USERNAME/ai-picture-book.git`
- SSH: `git@github.com:YOUR_USERNAME/ai-picture-book.git`

### 3️⃣ 推送代码

将下面的命令中的 `YOUR_USERNAME` 替换为你的用户名，然后运行：

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-picture-book.git
git push -u origin master
```

## 完成！✨

推送成功后访问你的仓库查看：
`https://github.com/YOUR_USERNAME/ai-picture-book`

---

**需要详细说明?** 查看 [GITHUB_SETUP.md](GITHUB_SETUP.md)

**遇到问题?** 运行 `python setup_github.py` 获取帮助
