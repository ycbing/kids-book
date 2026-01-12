# 部署文档索引

## 📚 部署文档总览

本目录包含AI绘本创作平台的完整部署文档和脚本。

---

## 📖 文档

### 1. [生产环境部署指南](./docs/DEPLOYMENT.md)
完整的部署文档，包含：
- 环境要求
- 部署前准备
- 快速部署指南
- 详细配置说明
- 反向代理配置
- 监控和维护
- 备份和恢复
- 故障排查

**查看文档**: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

### 2. [Nginx配置示例](./deploy/nginx/picturebook.conf)
生产环境Nginx配置文件，包含：
- HTTPS/SSL配置
- 反向代理设置
- WebSocket支持
- 安全头部配置
- 静态文件服务
- 监控端点保护

**文件位置**: [deploy/nginx/picturebook.conf](./deploy/nginx/picturebook.conf)

---

## 🛠️ 部署脚本

### Linux/macOS脚本

| 脚本 | 说明 | 使用方法 |
|------|------|----------|
| [scripts/deploy.sh](./scripts/deploy.sh) | 自动部署脚本 | `./scripts/deploy.sh` |
| [scripts/backup.sh](./scripts/backup.sh) | 数据库备份 | `./scripts/backup.sh` |
| [scripts/restore.sh](./scripts/restore.sh) | 数据库恢复 | `./scripts/restore.sh <backup-file>` |
| [scripts/health-check.sh](./scripts/health-check.sh) | 健康检查 | `./scripts/health-check.sh` |

### Windows脚本

| 脚本 | 说明 | 使用方法 |
|------|------|----------|
| [scripts/deploy.bat](./scripts/deploy.bat) | Windows部署脚本 | 双击运行或 `scripts\deploy.bat` |

---

## 🚀 快速开始

### 一键部署（Linux/macOS）

```bash
# 1. 克隆代码
git clone https://github.com/your-org/ai-picture-book.git
cd ai-picture-book

# 2. 配置环境变量
cp .env.example .env
vim .env  # 编辑配置

# 3. 运行部署脚本
chmod +x scripts/*.sh
./scripts/deploy.sh
```

### 一键部署（Windows）

```batch
# 1. 克隆代码
git clone https://github.com/your-org/ai-picture-book.git
cd ai-picture-book

# 2. 配置环境变量
copy .env.example .env
notepad .env  # 编辑配置

# 3. 运行部署脚本
scripts\deploy.bat
```

---

## 📋 部署检查清单

部署前检查：

- [ ] Docker已安装并运行
- [ ] Docker Compose已安装
- [ ] `.env`文件已配置
- [ ] 必需的环境变量已设置
- [ ] 端口8000、3000、5432、6379未被占用

部署后检查：

- [ ] 服务正常运行 (`docker-compose ps`)
- [ ] 健康检查通过 (`curl http://localhost:8000/health`)
- [ ] API文档可访问 (`http://localhost:8000/docs`)
- [ ] 前端正常加载 (`http://localhost:3000`)
- [ ] 日志无错误 (`docker-compose logs`)

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f backend

# 查看服务状态
docker-compose ps
```

### 数据库操作

```bash
# 备份数据库
./scripts/backup.sh

# 恢复数据库
./scripts/restore.sh ./backups/postgres/picturebook_20240101.sql.gz

# 进入数据库
docker exec -it picturebook-db psql -U picturebook
```

### 监控

```bash
# 健康检查
./scripts/health-check.sh

# 查看容器资源使用
docker stats

# 查看Celery任务（Flower）
# 访问 http://localhost:5555
```

---

## 📞 获取帮助

遇到问题？

1. 查看 [部署指南](./docs/DEPLOYMENT.md) 的故障排查章节
2. 检查服务日志: `docker-compose logs -f`
3. 运行健康检查: `./scripts/health-check.sh`
4. 提交Issue: [GitHub Issues](https://github.com/your-org/ai-picture-book/issues)

---

## 🔒 安全提示

生产环境部署前请务必：

1. 修改默认的`SECRET_KEY`
2. 设置强密码
3. 启用HTTPS（使用Let's Encrypt）
4. 配置防火墙规则
5. 限制敏感端点访问
6. 启用定期备份
7. 配置监控告警

---

**文档版本**: 1.0.0
**更新时间**: 2026-01-12
