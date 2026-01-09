# 依赖版本管理指南

## 实施时间
2026-01-09

---

## 📋 目录

- [概述](#概述)
- [Python依赖管理](#python依赖管理)
- [Node.js依赖管理](#nodejs依赖管理)
- [自动化安全检查](#自动化安全检查)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

---

## 概述

### 为什么需要依赖版本管理？

依赖版本管理对于生产环境的应用至关重要：

- ✅ **可重复构建**: 确保在不同环境安装完全相同的依赖版本
- ✅ **安全性**: 及时发现和修复安全漏洞
- ✅ **稳定性**: 避免意外的破坏性更新
- ✅ **可维护性**: 清晰的依赖关系和更新记录

### 版本管理策略

#### 1. 版本范围（requirements.txt, package.json）

用于开发环境，定义允许的版本范围：

```
fastapi>=0.104.1,<1.0.0  # Python
"react": "^18.2.0"        # Node.js
```

#### 2. 版本锁定（requirements.lock, package-lock.json）

用于生产环境，锁定精确版本：

```
fastapi==0.104.1          # Python
"react": "18.2.0"         # Node.js
```

---

## Python依赖管理

### 文件结构

```
backend/
├── requirements.txt      # 灵活版本（开发）
├── requirements.lock     # 精确版本（生产）
└── scripts/
    └── lock_requirements.py  # 锁定脚本
```

### 版本规范

#### requirements.txt（灵活版本）

```txt
# 使用 >= 定义最低版本
fastapi>=0.104.1

# 使用 < 限制主版本，避免破坏性更新
fastapi>=0.104.1,<1.0.0

# 推荐格式
包名>=最低版本,<下一个主版本.0
```

**优点**:
- 允许小版本和补丁更新（包含bug修复）
- 防止破坏性的主版本更新
- 兼容性与安全性的平衡

#### requirements.lock（精确版本）

```txt
# 精确锁定每个包的版本
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
```

**用途**:
- 生产环境部署
- CI/CD流水线
- Docker镜像构建

### 使用指南

#### 1. 安装依赖（开发环境）

```bash
cd backend

# 安装requirements.txt中的最新兼容版本
pip install -r requirements.txt

# 或使用精确版本（生产环境）
pip install -r requirements.lock
```

#### 2. 更新锁定文件

```bash
# 方法1: 使用自动脚本（推荐）
python scripts/lock_requirements.py

# 方法2: 手动更新
pip install -r requirements.txt --upgrade
pip freeze > requirements.lock

# 方法3: 更新到最新版本
python scripts/lock_requirements.py --update
```

#### 3. 检查版本变化

```bash
# 仅检查，不生成锁定文件
python scripts/lock_requirements.py --check
```

#### 4. 安全检查

```bash
# 使用Safety检查已知漏洞
pip install safety
safety check

# 使用pip-audit
pip install pip-audit
pip-audit
```

### 脚本功能说明

**`backend/scripts/lock_requirements.py`**:

```bash
# 生成锁定文件
python scripts/lock_requirements.py

# 检查版本变化
python scripts/lock_requirements.py --check

# 更新所有依赖到最新版本
python scripts/lock_requirements.py --update
```

**功能**:
- ✅ 自动生成精确版本锁定
- ✅ 检测版本变化
- ✅ 智能过滤不必要的包
- ✅ 生成带时间戳的锁定文件

---

## Node.js依赖管理

### 文件结构

```
frontend/
├── package.json          # 依赖定义和脚本
├── package-lock.json     # 精确版本锁定（自动生成）
└── scripts/
    ├── check-deps.sh     # Linux/Mac依赖管理脚本
    └── check-deps.bat    # Windows依赖管理脚本
```

### package.json配置

#### 1. 依赖版本格式

```json
{
  "dependencies": {
    "react": "^18.2.0",     // 允许更新18.x.x版本
    "axios": "~1.6.2",      // 只允许更新1.6.x补丁
    "lodash": "4.17.21"     // 精确版本，不更新
  },
  "devDependencies": {
    "typescript": "^5.3.2"
  }
}
```

**版本符号说明**:
- `^1.2.3`: 兼容更新（1.x.x，不改变最左边的非零数字）
- `~1.2.3`: 补丁更新（1.2.x，只更新补丁版本）
- `1.2.3`: 精确版本（不更新）
- `*`: 最新版本（不推荐）
- `latest`: 最新版本（不推荐）

#### 2. 引擎限制

```json
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

**作用**:
- 确保项目在兼容的Node/npm版本上运行
- npm install时会检查并警告版本不匹配

#### 3. 依赖管理脚本

```json
{
  "scripts": {
    "audit": "npm audit",
    "audit:fix": "npm audit fix",
    "audit:strict": "npm audit --audit-level=moderate",
    "outdated": "npm outdated",
    "update": "npm update",
    "deps:update": "npm update && npm run audit:fix",
    "check:updates": "npx npm-check-updates -u"
  }
}
```

### 使用指南

#### 1. 安装依赖

```bash
cd frontend

# 开发环境（使用package-lock.json）
npm install

# 生产环境（只安装dependencies）
npm install --production

# 清除缓存重新安装
npm ci
```

#### 2. 检查过时的依赖

```bash
# 查看过时的包
npm outdated

# 检查可用的主版本更新
npm run check:updates
```

**输出示例**:
```
Package            Current  Wanted  Latest  Location
axios              1.6.2    1.6.3   1.6.5   frontend
react              18.2.0   18.2.0  19.0.0  frontend
```

#### 3. 安全审计

```bash
# 检查安全漏洞
npm audit

# 自动修复可修复的漏洞
npm audit fix

# 强制修复（可能破坏性更改）
npm audit fix --force

# 只显示高危漏洞
npm run audit:strict
```

#### 4. 更新依赖

```bash
# 更新所有依赖到最新的兼容版本
npm update

# 使用npm-check-updates更新package.json
npx npm-check-updates -u
npm install

# 更新特定包
npm update axios
```

#### 5. 使用交互式脚本

**Linux/Mac**:
```bash
chmod +x frontend/scripts/check-deps.sh
./frontend/scripts/check-deps.sh
```

**Windows**:
```cmd
frontend\scripts\check-deps.bat
```

**脚本功能**:
- 检查Node和npm版本
- 检查过时的依赖
- 运行安全审计
- 更新依赖
- 清理依赖

---

## 自动化安全检查

### GitHub Actions工作流

**文件**: [`.github/workflows/dependency-check.yml`](.github/workflows/dependency-check.yml)

#### 触发条件

1. **定期检查**: 每周日UTC 00:00
2. **手动触发**: 在GitHub Actions页面手动运行
3. **PR触发**: 当依赖文件变化时

#### 检查内容

**Python后端**:
- ✅ Safety安全检查（已知漏洞数据库）
- ✅ pip-audit审计
- ✅ 依赖版本一致性检查
- ✅ 包统计信息

**Node前端**:
- ✅ npm audit安全审计
- ✅ 过时依赖检查
- ✅ 依赖统计
- ✅ 版本变化验证

#### 报告输出

检查完成后，会在以下位置生成报告：

1. **GitHub Summary**: 在Actions运行页面查看摘要
2. **Artifacts**: 下载详细的JSON报告
   - `python-security-reports`
   - `node-security-reports`

#### 配置本地CI

如果你使用其他CI系统：

```bash
# 在CI脚本中添加
pip install safety
safety check

npm audit --audit-level=high
```

---

## 最佳实践

### ✅ 推荐做法

#### 1. 定期更新依赖

**频率**: 每月至少一次

**流程**:
```bash
# 1. 检查可用更新
npm outdated  # 前端
pip list --outdated  # 后端

# 2. 查看更新日志
# 访问项目的GitHub Release页面

# 3. 测试环境更新
npm update  # 前端
pip install -r requirements.txt --upgrade  # 后端

# 4. 运行测试
npm test
pytest

# 5. 更新锁定文件
npm install  # 前端（更新package-lock.json）
python scripts/lock_requirements.py  # 后端
```

#### 2. 使用版本范围，而非精确版本

**package.json / requirements.txt**:
```json
// ✅ 好
"react": "^18.2.0"

// ❌ 不好
"react": "18.2.0"
```

**原因**:
- 自动获得安全修复和bug修复
- 减少手动维护工作量

**例外**: 生产环境使用`package-lock.json`和`requirements.lock`锁定精确版本

#### 3. 提交锁定文件

```bash
# ✅ 应该提交
git add package-lock.json
git add requirements.lock
git commit -m "更新依赖锁定文件"
```

**原因**:
- 确保团队使用相同版本
- CI/CD环境可重复构建
- 安全审计的基准

#### 4. 分离开发和生产依赖

**Python**:
- `requirements.txt`: 生产依赖
- `requirements-dev.txt`: 开发依赖（pytest, black等）

**Node.js**:
- `dependencies`: 生产依赖
- `devDependencies`: 开发依赖（testing-library, vite等）

#### 5. 审查安全警告

**流程**:
```bash
# 1. 运行审计
npm audit

# 2. 查看报告
npm audit --json

# 3. 判断严重程度
# - 高危/严重: 立即修复
# - 中危: 计划修复
# - 低危: 可接受

# 4. 应用修复
npm audit fix

# 5. 验证修复
npm audit
```

#### 6. 使用依赖更新工具

**npm-check-updates** (Node.js):
```bash
# 检查所有依赖的最新版本
npx npm-check-updates

# 更新package.json到最新版本
npx npm-check-updates -u
npm install
```

**pip-tools** (Python):
```bash
pip install pip-tools
pip-compile requirements.txt --output-file requirements.lock
```

### ❌ 避免的做法

#### 1. 不要忽略package-lock.json

```bash
# ❌ 不好
echo "package-lock.json" >> .gitignore

# ✅ 好
git add package-lock.json
git commit -m "锁定依赖版本"
```

#### 2. 不要混合包管理器

```bash
# ❌ 不好
npm install yarn
yarn install
pnpm install

# ✅ 好
# 团队统一使用npm
npm install
```

#### 3. 不要在生产环境使用latest或*

```json
// ❌ 不好
"express": "latest"
"lodash": "*"

// ✅ 好
"express": "^4.18.2"
"lodash": "^4.17.21"
```

#### 4. 不要盲目更新

```bash
# ❌ 不好
npm update
git commit -m "更新依赖"
git push  # 直接推送到生产

# ✅ 好
npm update
npm test  # 运行测试
# 手动测试应用
git commit -m "更新依赖到x.y.z"
# 创建PR，代码审查后再合并
```

#### 5. 不要忽略devDependencies

```json
// ❌ 不好
{
  "dependencies": {
    "jest": "^29.0.0"  // 测试框架应在devDependencies
  }
}

// ✅ 好
{
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
```

---

## 故障排查

### 问题1: 依赖冲突

**症状**:
```
npm ERR! peer dep missing: react@^18.0.0, required by react-dom@18.2.0
```

**解决方案**:

1. 检查冲突的包
```bash
npm ls react
```

2. 手动安装兼容版本
```bash
npm install react@^18.0.0
```

3. 使用resolutions（package.json）
```json
{
  "overrides": {
    "react": "^18.2.0"
  }
}
```

### 问题2: requirements.lock过时

**症状**: requirements.txt和requirements.lock不一致

**解决方案**:
```bash
# 重新生成锁定文件
pip install -r requirements.txt
python scripts/lock_requirements.py
```

### 问题3: npm audit报告大量漏洞

**症状**: `npm audit`显示几十个漏洞

**解决方案**:

1. **评估严重程度**:
```bash
npm audit --audit-level high
```

2. **自动修复可修复的**:
```bash
npm audit fix
```

3. **手动修复其余的**:
```bash
npm update package-name
```

4. **无法修复的**:
   - 检查是否为误报
   - 查看上游项目的issue
   - 考虑替换依赖

### 问题4: pip安装失败

**症状**:
```
ERROR: Could not find a version that satisfies the requirement
```

**解决方案**:

1. **升级pip**:
```bash
pip install --upgrade pip
```

2. **清除缓存**:
```bash
pip cache purge
```

3. **检查Python版本**:
```bash
python --version  # 确保版本兼容
```

4. **使用国内镜像**（如果网络问题）:
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题5: npm install很慢

**解决方案**:

1. **使用npm ci**（更快、更可靠）:
```bash
npm ci
```

2. **使用国内镜像**:
```bash
npm config set registry https://registry.npmmirror.com
```

3. **并行安装**（仅npm ci支持）:
```bash
npm ci --prefer-offline --no-audit
```

### 问题6: Docker构建时依赖安装失败

**症状**: Docker构建时pip install或npm install失败

**解决方案**:

1. **使用层缓存**（Dockerfile优化）:
```dockerfile
# 先复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 再复制代码
COPY . .
```

2. **使用锁定文件**:
```dockerfile
COPY requirements.lock .
RUN pip install -r requirements.lock
```

3. **国内镜像**（如果在中国）:
```dockerfile
RUN pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📊 依赖管理检查清单

### 日常维护

- [ ] 每月检查一次过时的依赖
- [ ] 每周运行一次安全审计
- [ ] 及时更新锁定文件
- [ ] 查看依赖的更新日志

### 发布前

- [ ] 运行完整测试套件
- [ ] 执行安全审计
- [ ] 更新锁定文件
- [ ] 检查依赖更新公告
- [ ] 在staging环境验证

### CI/CD

- [ ] 配置自动化安全检查
- [ ] PR时检查依赖变化
- [ ] 定期运行依赖扫描
- [ ] 保存审计报告

---

## 🔧 高级配置

### 1. 私有npm包

```bash
# 使用.npmrc
npm config set @your-scope:registry https://your-registry.com
```

### 2. 私有Python包

```bash
# 使用pip配置
pip config set global.index-url https://your-pypi-server.com
```

### 3. Monorepo依赖管理

```bash
# 使用pnpm workspace
pnpm install

# 或使用Yarn workspaces
yarn install
```

### 4. 依赖许可检查

```bash
# Python
pip install liccheck
liccheck -s liccheck.ini

# Node.js
npx license-checker
```

---

## 📚 相关资源

### 官方文档

- [npm语义化版本](https://docs.npmjs.com/cli/v6/using-npm/semver)
- [pip需求说明符](https://pip.pypa.io/en/stable/reference/requirement-specifiers/)
- [Python包索引(PyPI)](https://pypi.org/)
- [npm registry](https://www.npmjs.com/)

### 安全工具

- [Safety (Python)](https://github.com/pyupio/safety)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [npm audit](https://docs.npmjs.com/cli/audit)
- [Snyk](https://snyk.io/)

### 依赖更新工具

- [npm-check-updates](https://github.com/raineorshine/npm-check-updates)
- [pip-tools](https://github.com/jazzband/pip-tools)
- [Renovate Bot](https://github.com/renovatebot/renovate)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)

---

## 📊 完成状态

| 任务 | 状态 |
|------|------|
| 创建Python依赖锁定机制 | ✅ 完成 |
| 更新Node.js依赖管理脚本 | ✅ 完成 |
| 创建自动化安全检查工作流 | ✅ 完成 |
| 编写依赖管理文档 | ✅ 完成 |

**整体进度**: 4/4 (100%)

---

**实施完成时间**: 2026-01-09
**实施者**: Claude Code
**优化类型**: 依赖版本管理
**安全性**: ⭐⭐⭐⭐⭐ 显著提升
**稳定性**: ⭐⭐⭐⭐⭐ 显著提升
**可维护性**: ⭐⭐⭐⭐⭐ 显著提升
