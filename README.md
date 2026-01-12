# 1. 克隆项目
git clone <repository-url>
cd ai-picture-book

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

# 3. 使用Docker启动
docker-compose up -d

# 4. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/docs


# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev

---

## 📚 生产环境部署

### 快速部署

```bash
# 使用自动部署脚本
./scripts/deploy.sh        # Linux/macOS
scripts\deploy.bat         # Windows
```

### 详细文档

完整的部署文档请查看：
- 📖 [部署文档索引](./DEPLOYMENT_INDEX.md)
- 🚀 [生产环境部署指南](./docs/DEPLOYMENT.md)
- ⚙️ [Nginx配置示例](./deploy/nginx/picturebook.conf)

### 部署脚本

| 脚本 | 说明 |
|------|------|
| `scripts/deploy.sh` | 自动部署脚本 |
| `scripts/backup.sh` | 数据库备份 |
| `scripts/restore.sh` | 数据库恢复 |
| `scripts/health-check.sh` | 健康检查 |

---

## 📋 其他文档

- [API优化实施指南](./API_OPTIMIZATION.md)
- [数据库优化实施指南](./DATABASE_OPTIMIZATION.md)
- [前端性能优化指南](./FRONTEND_OPTIMIZATION.md)
- [API文档完善指南](./API_DOCUMENTATION.md)
- [监控和告警配置](./MONITORING_AND_ALERTING.md)
- [依赖版本管理](./DEPENDENCY_VERSION_MANAGEMENT.md)
