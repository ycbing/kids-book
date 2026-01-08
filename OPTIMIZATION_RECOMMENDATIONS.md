# AI绘本平台项目优化建议报告

> 本文档基于对整个项目的全面代码审查和架构分析，提供了系统性的优化建议。

**生成时间**: 2026-01-08
**项目版本**: v1.0.0
**审查范围**: 前端 + 后端 + 配置 + 部署

---

## 📋 目录

- [高优先级（安全问题）](#高优先级安全问题)
- [中优先级（架构与性能）](#中优先级架构与性能)
- [低优先级（代码质量）](#低优先级代码质量)
- [DevOps优化](#devops优化)
- [性能优化建议](#性能优化建议)
- [文档优化](#文档优化)
- [优化优先级建议](#优化优先级建议)

---

## 🔴 高优先级（安全问题）

### 1. 敏感信息泄露

**位置**: [backend/app/config.py:16-21]

**问题描述**:
```python
TEXT_API_KEY: Optional[str] = "sk-lrblpprkvitjenoutducitdhqogfhsfyiziwqvovwftfrfym"
IMAGE_API_KEY: Optional[str] = "sk-lrblpprkvitjenoutducitdhqogfhsfyiziwqvovwftfrfym"
```
API密钥硬编码在源代码中，存在严重的安全风险。

**风险等级**: ⚠️ 严重
- 代码泄露会导致密钥泄露
- API密钥被滥用导致费用损失
- 无法在不修改代码的情况下更换密钥

**修复方案**:
```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 移除默认值，强制从环境变量读取
    TEXT_API_KEY: Optional[str] = None
    IMAGE_API_KEY: Optional[str] = None
    # ... 其他配置

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 启动时验证必需的环境变量
        self._validate_required_vars()

    def _validate_required_vars(self):
        required = ['TEXT_API_KEY', 'IMAGE_API_KEY']
        missing = [v for v in required if not getattr(self, v)]
        if missing:
            raise ValueError(
                f"缺少必需的环境变量: {', '.join(missing)}\n"
                f"请在 .env 文件中配置这些变量"
            )
```

**环境变量配置** (backend/.env):
```env
# AI服务配置
TEXT_API_KEY=your_api_key_here
IMAGE_API_KEY=your_api_key_here
TEXT_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_BASE_URL=https://api.siliconflow.cn/v1
```

**验证步骤**:
1. 创建 `.gitignore` 规则: `backend/.env`
2. 从 config.py 移除硬编码密钥
3. 在 `.env` 文件中配置密钥
4. 提供示例文件 `.env.example`

---

### 2. CORS配置过于宽松

**位置**: [backend/app/main.py:106]

**问题描述**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险等级**: ⚠️ 高
- 任何网站都可以向你的API发送请求
- 可能导致CSRF攻击
- 暴露API端点给恶意使用者

**修复方案**:
```python
# backend/app/main.py
import os

# 从环境变量读取允许的域名
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**环境变量配置**:
```env
# 开发环境
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# 生产环境
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

### 3. 缺少用户认证系统

**位置**: [backend/app/api/routes.py]

**问题描述**:
- 所有API端点都是公开的，没有身份验证
- 使用硬编码的 `user_id = 1`
- 无法区分不同用户的资源

**风险等级**: ⚠️ 高
- 任何人都可以访问、修改、删除他人的绘本
- 无法追踪用户行为
- 资源隔离缺失

**修复方案**:

#### 3.1 添加认证依赖
```python
# backend/app/api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """验证JWT token并返回user_id"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )

# 在路由中使用
async def get_current_user(user_id: int = Depends(verify_token)) -> User:
    """获取当前登录用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
```

#### 3.2 添加认证端点
```python
# backend/app/api/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["认证"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
async def register(
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查用户是否存在
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")

    # 创建用户
    hashed_password = pwd_context.hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()

    # 生成token
    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
```

#### 3.3 保护现有路由
```python
# backend/app/api/routes.py
from app.api.auth import get_current_user

@router.post("/books", response_model=BookResponse)
async def create_book(
    request: BookCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 添加认证
):
    # 使用 current_user.id 而不是硬编码的 1
    book = await book_service.create_book(db, request, current_user.id)
    # ...
```

---

## 🟠 中优先级（架构与性能）

### 后端优化

#### 4. 数据库连接管理优化

**位置**: [backend/app/models/database.py:10]

**问题描述**:
```python
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
```
- SQLite不适合生产环境（并发写入限制）
- 缺少连接池配置
- 没有数据库健康检查

**修复方案**:

##### 4.1 支持多数据库配置
```python
# backend/app/config.py
class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./picturebook.db"

    # 生产环境建议使用PostgreSQL
    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def database_connect_args(self) -> dict:
        if self.is_sqlite:
            return {"check_same_thread": False}
        return {}
```

##### 4.2 添加连接池
```python
# backend/app/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=settings.database_connect_args,
    poolclass=QueuePool,
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查有效性
    echo=settings.DEBUG  # 开发环境打印SQL
)
```

##### 4.3 生产环境配置
```env
# 开发环境 - SQLite
DATABASE_URL=sqlite:///./picturebook.db

# 生产环境 - PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/picturebook
```

---

#### 5. 统一错误处理机制

**位置**: [backend/app/api/routes.py]

**问题描述**:
- 错误处理方式不一致
- 缺少统一的错误响应格式
- 堆栈信息可能暴露给客户端

**修复方案**:

##### 5.1 创建统一异常类
```python
# backend/app/core/exceptions.py
from typing import Optional

class AppException(Exception):
    """应用基础异常类"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, 404, "NOT_FOUND")

class BadRequestException(AppException):
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(message, 400, "BAD_REQUEST")

class UnauthorizedException(AppException):
    def __init__(self, message: str = "未授权访问"):
        super().__init__(message, 401, "UNAUTHORIZED")

class ForbiddenException(AppException):
    def __init__(self, message: str = "无权限访问"):
        super().__init__(message, 403, "FORBIDDEN")
```

##### 5.2 全局异常处理器
```python
# backend/app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义应用异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message
            },
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)

    # 生产环境不返回详细错误信息
    error_detail = str(exc) if settings.DEBUG else "服务器内部错误"

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": error_detail
            },
            "path": request.url.path
        }
    )
```

##### 5.3 在服务中使用
```python
# backend/app/services/book_service.py
from app.core.exceptions import NotFoundException

def get_book(self, db: Session, book_id: int):
    book = db.query(PictureBook).filter(PictureBook.id == book_id).first()
    if not book:
        raise NotFoundException(f"绘本 {book_id} 不存在")
    return book
```

---

#### 6. API限流和请求验证

**问题描述**:
- 缺少API限流机制
- 没有请求频率限制
- 容易被滥用或DDoS攻击

**修复方案**:

##### 6.1 使用Redis实现限流
```python
# backend/app/core/rate_limit.py
from fastapi import Request, HTTPException
import redis
import asyncio

redis_client = redis.from_url(settings.REDIS_URL)

async def rate_limit(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """API限流中间件"""
    # 识别用户（优先使用真实IP）
    client_ip = request.client.host
    user_id = request.state.get("user_id")

    # 使用user_id或IP作为限流key
    limit_key = f"rate_limit:{user_id or client_ip}"

    try:
        # 增加计数
        current = redis_client.incr(limit_key)

        # 第一次请求时设置过期时间
        if current == 1:
            redis_client.expire(limit_key, window_seconds)

        # 超过限制
        if current > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请稍后再试。限制：{max_requests}次/{window_seconds}秒"
            )
    except Exception as e:
        # Redis失败时记录日志但不阻止请求
        logger.error(f"限流Redis错误: {e}")
```

##### 6.2 应用限流
```python
# backend/app/api/routes.py
from app.core.rate_limit import rate_limit

@router.post("/books")
@rate_limit(max_requests=10, window_seconds=60)  # 每分钟最多10次
async def create_book(...):
    ...
```

---

#### 7. 实现任务队列

**位置**: [backend/requirements.txt:14] - 已安装Celery但未使用

**问题描述**:
- 绘本生成是耗时操作（可能需要几分钟）
- 当前使用FastAPI的BackgroundTasks，不适合长时间任务
- 服务重启会丢失正在进行的任务

**修复方案**:

##### 7.1 配置Celery
```python
# backend/app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    "ai_picture_book",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
)
```

##### 7.2 创建异步任务
```python
# backend/app/tasks/book_tasks.py
from app.core.celery_app import celery_app
from app.models.database import SessionLocal
from app.services.book_service import book_service

@celery_app.task(bind=True)
def generate_book_task(self, book_id: int, request_data: dict):
    """异步生成绘本任务"""
    db = SessionLocal()

    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'stage': '初始化', 'progress': 0})

        # 生成绘本内容
        book = book_service.generate_book_content(
            db,
            book_id,
            request_data,
            progress_callback=lambda stage, progress: self.update_state(
                state='PROGRESS',
                meta={'stage': stage, 'progress': progress}
            )
        )

        return {'status': 'SUCCESS', 'book_id': book_id}

    except Exception as e:
        return {'status': 'FAILED', 'error': str(e)}
    finally:
        db.close()
```

##### 7.3 修改API端点
```python
# backend/app/api/routes.py
from app.tasks.book_tasks import generate_book_task

@router.post("/books", response_model=BookResponse)
async def create_book(
    request: BookCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建绘本并启动异步生成任务"""
    # 创建绘本记录
    book = await book_service.create_book(db, request, current_user.id)

    # 启动Celery任务
    task = generate_book_task.delay(book.id, request.dict())

    # 返回任务ID
    return {
        "book_id": book.id,
        "task_id": task.id,
        "status": "generating"
    }

@router.get("/books/{book_id}/task-status")
async def get_task_status(book_id: int, task_id: str):
    """查询任务状态"""
    from app.core.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.info if result.state != 'PENDING' else None
    }
```

##### 7.4 启动Celery Worker
```bash
# backend/start_celery.sh
celery -A app.core.celery_app worker --loglevel=info
```

---

#### 8. 日志系统优化

**位置**: [backend/app/main.py:15-22]

**问题描述**:
- 日志格式不够结构化
- 缺少日志轮转
- 开发/生产环境使用相同配置
- 缺少请求追踪

**修复方案**:

##### 8.1 结构化日志
```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data, ensure_ascii=False)

def setup_logging():
    """配置应用日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ) if settings.DEBUG else JSONFormatter()
    )
    logger.addHandler(console_handler)

    # 文件处理器（仅生产环境）
    if not settings.DEBUG:
        from logging.handlers import RotatingFileHandler

        # 应用日志
        app_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        app_handler.setFormatter(JSONFormatter())
        logger.addHandler(app_handler)

        # 错误日志
        error_handler = RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10*1024*1024,
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)
```

##### 8.2 添加请求追踪
```python
# backend/app/main.py
import uuid

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """请求中间件 - 添加请求ID"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 添加请求ID到日志
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={"request_id": request_id}
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response
```

---

#### 9. 文件上传安全

**位置**: [backend/app/api/routes.py]

**问题描述**:
- 缺少文件类型验证
- 没有文件大小限制
- 缺少病毒扫描

**修复方案**:

```python
# backend/app/core/file_utils.py
import os
from pathlib import Path
from typing import Set
import aiofiles
from fastapi import UploadFile, HTTPException

ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg", "image/png", "image/gif", "image/webp"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def validate_upload_file(file: UploadFile) -> None:
    """验证上传的文件"""
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大允许: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # 重置文件指针
    await file.seek(0)

    # 验证MIME类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的文件类型: {file.content_type}"
        )

async def save_upload_file(
    file: UploadFile,
    destination: Path,
    max_size: int = MAX_FILE_SIZE
) -> str:
    """安全地保存上传文件"""
    # 验证文件
    await validate_upload_file(file)

    # 创建安全的文件名
    safe_filename = Path(file.filename).name
    destination_path = destination / safe_filename

    # 确保目标路径在上传目录内
    if not str(destination_path).startswith(str(destination.resolve())):
        raise HTTPException(status_code=400, detail="无效的文件路径")

    # 保存文件
    destination.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(destination_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return str(destination_path)
```

---

### 前端优化

#### 10. 状态管理优化

**位置**: [frontend/src/stores/bookStore.ts]

**问题描述**:
- 同时使用轮询和WebSocket，造成冗余请求
- WebSocket断线后没有自动重连
- 状态更新逻辑复杂

**修复方案**:

##### 10.1 优化WebSocket服务
```typescript
// frontend/src/services/websocket.ts
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private subscribers: Set<(message: WebSocketMessage) => void> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  connect(bookId: number) {
    // 如果已连接，先断开
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://localhost:8000/api/v1/ws/book_${bookId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.notifySubscribers(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(bookId);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private attemptReconnect(bookId: number) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      this.reconnectTimer = setTimeout(() => {
        this.connect(bookId);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      // 切换到轮询模式作为降级方案
      this.enablePollingMode(bookId);
    }
  }

  private enablePollingMode(bookId: number) {
    // WebSocket失败后降级到轮询
    console.log('Falling back to polling mode');
    // 实现轮询逻辑
  }

  subscribe(callback: (message: WebSocketMessage) => void): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  private notifySubscribers(message: WebSocketMessage) {
    this.subscribers.forEach(callback => callback(message));
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// 导出单例
export const websocketService = new WebSocketService();
```

##### 10.2 简化Store
```typescript
// frontend/src/stores/bookStore.ts
export const useBookStore = create<BookState>((set, get) => ({
  // 移除轮询相关状态
  // pollingInterval: null,  // 删除

  // 保留WebSocket逻辑，移除轮询逻辑
  connectWebSocket: (bookId: number) => {
    get().disconnectWebSocket();
    websocketService.connect(bookId);

    const unsubscribe = websocketService.subscribe((message) => {
      get().handleWebSocketMessage(message);
    });

    set({ websocketUnsubscribe: unsubscribe });
  },

  // 移除 startPolling 和 stopPolling
  // 使用纯WebSocket实时更新
}));
```

---

#### 11. 添加全局错误处理

**位置**: [frontend/src/services/api.ts]

**问题描述**:
- 每个请求都要单独处理错误
- 缺少统一的重试机制
- 错误消息不友好

**修复方案**:

```typescript
// frontend/src/services/api.ts
import axios, { AxiosError } from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加请求ID
    config.headers['X-Request-ID'] = generateUUID();

    // 添加认证token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // 处理401未授权
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // 尝试刷新token
      try {
        const newToken = await refreshAuthToken();
        localStorage.setItem('auth_token', newToken);

        // 重试原始请求
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 网络错误重试
    if (!error.response && !originalRequest._retry) {
      originalRequest._retry = true;
      const retryDelay = 1000;

      await new Promise(resolve => setTimeout(resolve, retryDelay));
      return api(originalRequest);
    }

    // 格式化错误消息
    const errorMessage = formatErrorMessage(error);
    return Promise.reject(new Error(errorMessage));
  }
);

function formatErrorMessage(error: AxiosError): string {
  if (error.response) {
    const data = error.response.data as any;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (data?.detail) {
      return data.detail;
    }
    return `请求失败 (${error.response.status})`;
  }

  if (error.request) {
    return '网络错误，请检查连接';
  }

  return error.message || '未知错误';
}

// 自动刷新token
async function refreshAuthToken(): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await axios.post('/api/v1/auth/refresh', {
    refresh_token: refreshToken
  });
  return response.data.access_token;
}

export default api;
```

---

#### 12. 优化加载状态管理

**位置**: [frontend/src/stores/bookStore.ts]

**问题描述**:
- 各组件独立管理加载状态
- 缺少全局加载指示器
- 用户体验不一致

**修复方案**:

##### 12.1 创建全局加载状态
```typescript
// frontend/src/stores/uiStore.ts
interface UIState {
  globalLoading: boolean;
  loadingMessage: string;
  requests: Set<string>;

  setGlobalLoading: (loading: boolean, message?: string) => void;
  startRequest: (requestId: string) => void;
  endRequest: (requestId: string) => void;
  isLoading: (requestId: string) => boolean;
}

export const useUIStore = create<UIState>((set) => ({
  globalLoading: false,
  loadingMessage: '',
  requests: new Set(),

  setGlobalLoading: (loading, message = '加载中...') => {
    set({ globalLoading: loading, loadingMessage: message });
  },

  startRequest: (requestId: string) => {
    set((state) => ({
      requests: new Set([...state.requests, requestId])
    }));
  },

  endRequest: (requestId: string) => {
    set((state) => {
      const newRequests = new Set(state.requests);
      newRequests.delete(requestId);
      return { requests: newRequests };
    });
  },

  isLoading: (requestId: string) => {
    return get().requests.has(requestId);
  }
}));
```

##### 12.2 创建加载组件
```typescript
// frontend/src/components/Loading.tsx
import { useUIStore } from '../stores/uiStore';
import { Loader2 } from 'lucide-react';

export const GlobalLoading: React.FC = () => {
  const { globalLoading, loadingMessage } = useUIStore();

  if (!globalLoading) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 flex items-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        <span className="text-gray-700">{loadingMessage}</span>
      </div>
    </div>
  );
};

// 骨架屏组件
export const SkeletonCard: React.FC = () => (
  <div className="animate-pulse bg-gray-200 rounded-lg h-64" />
);
```

##### 12.3 使用示例
```typescript
// 在组件中使用
const { startRequest, endRequest } = useUIStore();

const fetchBooks = async () => {
  const requestId = 'fetchBooks';
  startRequest(requestId);

  try {
    const books = await bookApi.list();
    set({ books });
  } finally {
    endRequest(requestId);
  }
};
```

---

#### 13. 图片优化

**位置**: [frontend/src/components/BookViewer.tsx:202]

**问题描述**:
- 直接显示大图，加载慢
- 没有懒加载
- 缺少图片缓存策略

**修复方案**:

##### 13.1 图片懒加载组件
```typescript
// frontend/src/components/LazyImage.tsx
import { useState, useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className = '',
  placeholder = 'data:image/svg+xml,...'
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            img.src = src;
            observer.unobserve(img);
          }
        });
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [src]);

  return (
    <div className={`relative ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      )}

      {error ? (
        <div className="flex items-center justify-center h-full bg-gray-100">
          <span className="text-gray-400">图片加载失败</span>
        </div>
      ) : (
        <img
          ref={imgRef}
          src={placeholder}
          alt={alt}
          className={`transition-opacity duration-300 ${loading ? 'opacity-0' : 'opacity-100'}`}
          onLoad={() => setLoading(false)}
          onError={() => {
            setLoading(false);
            setError(true);
          }}
          loading="lazy"
        />
      )}
    </div>
  );
};
```

##### 13.2 响应式图片
```typescript
// frontend/src/components/ResponsiveImage.tsx
interface ResponsiveImageProps {
  src: string;
  alt: string;
  sizes?: string[];
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  alt,
  sizes = [400, 800, 1200]
}) => {
  // 生成不同尺寸的图片URL
  const srcSet = sizes.map(size =>
    `${src}?w=${size} ${size}w`
  ).join(', ');

  return (
    <img
      src={src}
      srcSet={srcSet}
      alt={alt}
      loading="lazy"
    />
  );
};
```

##### 13.3 在BookViewer中使用
```typescript
// frontend/src/components/BookViewer.tsx
import { LazyImage } from './LazyImage';

// 替换原有的img标签
<LazyImage
  src={page.image_url}
  alt={`第${page.page_number}页`}
  className="max-w-full max-h-[500px] rounded-lg shadow-lg"
/>
```

---

#### 14. 修复路由跳转

**位置**: [frontend/src/components/BookCreator.tsx:72]

**问题描述**:
```typescript
window.location.href = `/book/${book.id}`;
```
使用原生跳转，会刷新整个页面，丢失状态。

**修复方案**:

```typescript
// frontend/src/components/BookCreator.tsx
import { useNavigate } from 'react-router-dom';

export const BookCreator: React.FC = () => {
  const navigate = useNavigate();
  // ...

  const handleSubmit = async () => {
    try {
      const book = await createBook(formData);
      toast.success('绘本创建成功！正在生成内容...');

      // 使用React Router导航，不刷新页面
      navigate(`/book/${book.id}`, {
        state: { message: '绘本创建成功' }
      });
    } catch (error) {
      toast.error('创建失败，请重试');
    }
  };
};
```

---

## 🟡 低优先级（代码质量）

### 15. 类型安全提升

#### 后端类型注解
```python
# backend/app/api/routes.py
from typing import List

@router.get("/books", response_model=List[BookResponse])
async def list_books(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[BookResponse]:  # 添加返回类型
    """获取绘本列表"""
    # ...
```

#### 前端类型完善
```typescript
// frontend/src/services/api.ts
// 添加完整的接口定义
export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
  };
  path: string;
}

export interface APIResponse<T> {
  success: true;
  data: T;
}

// 泛型API方法
export const api = {
  get: async <T>(url: string): Promise<T> => {
    const response = await axios.get<APIResponse<T>>(url);
    return response.data.data;
  },
  // ...
};
```

---

### 16. 提取公共组件

**问题**: 多个组件中存在重复的loading/error UI

**解决方案**:

```typescript
// frontend/src/components/common/EmptyState.tsx
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action
}) => (
  <div className="text-center py-12">
    {icon && <div className="mb-4">{icon}</div>}
    <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
    {description && <p className="text-gray-500 mb-4">{description}</p>}
    {action}
  </div>
);

// 使用示例
<EmptyState
  icon={<BookOpen className="w-16 h-16 text-gray-300 mx-auto" />}
  title="还没有绘本"
  description="点击下方按钮开始创作你的第一个绘本吧"
  action={<Link to="/create">开始创作</Link>}
/>
```

---

### 17. 添加测试

#### 后端测试 (pytest)
```python
# tests/test_book_service.py
import pytest
from app.services.book_service import book_service
from app.models.database import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_book(db):
    """测试创建绘本"""
    from app.models.schemas import BookCreateRequest

    request = BookCreateRequest(
        theme="测试主题",
        keywords=["测试"],
        target_age="3-6岁",
        style="水彩风格",
        page_count=8
    )

    book = await book_service.create_book(db, request, user_id=1)

    assert book.id is not None
    assert book.theme == request.theme
    assert book.status == BookStatus.DRAFT

def test_get_book(db):
    """测试获取绘本"""
    book = book_service.get_book(db, 1)
    assert book is not None
    assert book.id == 1
```

#### 前端测试 (Vitest)
```typescript
// src/stores/__tests__/bookStore.test.ts
import { describe, it, expect, vi } from 'vitest';
import { useBookStore } from '../bookStore';

describe('BookStore', () => {
  it('should create book successfully', async () => {
    const store = useBookStore.getState();

    // Mock API
    vi.mock('../services/api', () => ({
      bookApi: {
        create: vi.fn().mockResolvedValue({ id: 1, title: 'Test Book' })
      }
    }));

    await store.createBook({
      theme: 'Test',
      keywords: [],
      target_age: '3-6岁',
      style: '水彩风格',
      page_count: 8
    });

    expect(store.currentBook?.id).toBe(1);
    expect(store.isGenerating).toBe(false);
  });
});
```

---

### 18. 环境变量验证

**问题**: 缺少启动时的环境变量验证

**解决方案**:

```python
# backend/app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时验证配置
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        raise SystemExit(1)

    logger.info("✅ 配置验证通过")
    # ...

# backend/app/config.py
class Settings(BaseSettings):
    # ...

    def validate(self):
        """验证必需的环境变量"""
        errors = []

        if not self.TEXT_API_KEY:
            errors.append("TEXT_API_KEY未设置")

        if not self.IMAGE_API_KEY:
            errors.append("IMAGE_API_KEY未设置")

        if errors:
            raise ValueError(
                "配置验证失败:\n" + "\n".join(f"- {e}" for e in errors)
            )

        # 验证API连接
        import asyncio
        from app.services.retry_helper import test_api_connection

        async def test_connections():
            text_ok = await test_api_connection(
                self.TEXT_BASE_URL,
                self.TEXT_API_KEY
            )
            if not text_ok:
                errors.append("文本API连接失败")

            image_ok = await test_api_connection(
                self.IMAGE_BASE_URL,
                self.IMAGE_API_KEY
            )
            if not image_ok:
                errors.append("图像API连接失败")

            if errors:
                raise ValueError("\n".join(errors))

        asyncio.run(test_connections())
```

---

## 🔧 DevOps优化

### 19. Docker健康检查

**位置**: [docker-compose.yml]

**问题描述**:
- 缺少健康检查
- 容器不健康时无法自动重启
- 无法准确判断服务状态

**修复方案**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/picturebook.db
      - TEXT_API_KEY=${TEXT_API_KEY}
      - IMAGE_API_KEY=${IMAGE_API_KEY}
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  redis_data:
```

---

### 20. 依赖版本管理

**位置**: [backend/requirements.txt, frontend/package.json]

**问题描述**:
- Python依赖没有版本锁定
- 前端依赖可能存在安全漏洞

**修复方案**:

##### 20.1 Python依赖
```bash
# 生成精确的版本锁定
pip freeze > requirements.lock

# requirements.txt (用于开发)
fastapi>=0.104.1,<1.0.0
uvicorn[standard]>=0.24.0,<1.0.0
# ...

# requirements.lock (用于生产，自动生成)
fastapi==0.104.1
uvicorn==0.24.0
# ...
```

##### 20.2 前端依赖
```json
// package.json
{
  "scripts": {
    "audit": "npm audit",
    "audit:fix": "npm audit fix",
    "outdated": "npm outdated",
    "update": "npm update"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

##### 20.3 自动化检查
```yaml
# .github/workflows/dependency-check.yml
name: Dependency Check

on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日检查
  workflow_dispatch:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Python security check
        run: |
          pip install safety
          safety check

      - name: Node security check
        run: npm audit --audit-level=high
```

---

### 21. 监控和告警

**建议实施方案**:

##### 21.1 性能监控 (Prometheus + Grafana)
```python
# backend/app/core/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator

def setup_metrics(app: FastAPI):
    Instrumentator().instrument(app).expose(app)

# backend/app/main.py
from app.core.metrics import setup_metrics

setup_metrics(app)
```

##### 21.2 错误追踪 (Sentry)
```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "development")
)
```

##### 21.3 健康检查端点
```python
# backend/app/api/health.py
from fastapi import APIRouter
from app.core.celery_app import celery_app
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    """详细健康检查"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # 检查数据库
    try:
        db.query(User).first()
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    # 检查Redis
    try:
        redis_client.ping()
        status["checks"]["redis"] = "ok"
    except Exception as e:
        status["checks"]["redis"] = f"error: {str(e)}"

    # 检查Celery
    try:
        celery_app.control.ping()
        status["checks"]["celery"] = "ok"
    except Exception as e:
        status["checks"]["celery"] = f"error: {str(e)}"

    # 返回相应状态码
    code = 200 if status["status"] == "healthy" else 503

    return status, code
```

---

## 📊 性能优化建议

### 22. 数据库优化

#### 22.1 添加索引
```python
# backend/app/models/database.py
class PictureBook(Base):
    __tablename__ = "picture_books"

    # ... 现有字段

    __table_args__ = (
        Index('idx_owner_created', 'owner_id', 'created_at'),
        Index('idx_status', 'status'),
    )
```

#### 22.2 查询优化
```python
# backend/app/services/book_service.py
from sqlalchemy.orm import joinedload

def get_user_books(db, user_id, skip, limit):
    """使用eager loading优化查询"""
    return db.query(PictureBook)\
        .options(joinedload(PictureBook.pages))\
        .filter(PictureBook.owner_id == user_id)\
        .order_by(PictureBook.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

#### 22.3 缓存层
```python
# backend/app/core/cache.py
from functools import wraps
import hashlib
import json

def cache_response(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{func.__name__}:{hash_args(args, kwargs)}"

            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

# 使用
@cache_response(ttl=600)
async def get_popular_books():
    # ...
```

---

### 23. API优化

#### 23.1 分页实现
```python
# backend/app/models/schemas.py
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# backend/app/api/routes.py
@router.get("/books")
async def list_books(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    total = db.query(PictureBook).count()
    books = db.query(PictureBook)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    return PaginatedResponse(
        items=books,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

#### 23.2 响应压缩
```python
# backend/app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 23.3 CDN配置
```python
# backend/app/config.py
class Settings(BaseSettings):
    # CDN配置
    CDN_DOMAIN: str = "https://cdn.yourdomain.com"
    USE_CDN: bool = False

    def get_cdn_url(self, path: str) -> str:
        if self.USE_CDN:
            return f"{self.CDN_DOMAIN}/{path}"
        return f"/{path}"
```

---

### 24. 前端性能优化

#### 24.1 代码分割
```typescript
// frontend/src/App.tsx
import { lazy, Suspense } from 'react';

const BookCreator = lazy(() => import('./components/BookCreator'));
const BookViewer = lazy(() => import('./components/BookViewer'));
const BookList = lazy(() => import('./components/BookList'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/create" element={<BookCreator />} />
        <Route path="/book/:id" element={<BookViewer />} />
        <Route path="/" element={<BookList />} />
      </Routes>
    </Suspense>
  );
}
```

#### 24.2 Bundle优化
```typescript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['framer-motion', 'lucide-react'],
          'utils': ['axios', 'zustand', '@tanstack/react-query']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
});
```

#### 24.3 Service Worker缓存
```typescript
// frontend/public/sw.js
const CACHE_NAME = 'ai-picture-book-v1';
const ASSETS = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
```

---

## 📝 文档优化

### 25. API文档完善

#### 25.1 增强OpenAPI文档
```python
# backend/app/api/routes.py
from fastapi import Body
from typing import List

@router.post(
    "/books",
    response_model=BookResponse,
    summary="创建新绘本",
    description="""
    创建一个新的AI绘本并开始生成内容。

    **流程**:
    1. 创建绘本记录（状态: draft）
    2. 启动后台生成任务
    3. 生成故事文本
    4. 生成配图
    5. 更新状态为completed

    **预计时间**: 8-16页绘本约需2-5分钟
    """,
    responses={
        200: {"description": "绘本创建成功"},
        400: {"description": "请求参数错误"},
        401: {"description": "未授权"},
        500: {"description": "服务器错误"}
    },
    tags=["绘本管理"]
)
async def create_book(
    request: BookCreateRequest = Body(
        ...,
        example={
            "theme": "小兔子学会分享",
            "keywords": ["友谊", "分享"],
            "target_age": "3-6岁",
            "style": "水彩风格",
            "page_count": 8
        }
    )
):
    """创建绘本并开始生成"""
    # ...
```

#### 25.2 Postman Collection
创建 `postman_collection.json`:

```json
{
  "info": {
    "name": "AI绘本平台API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "用户认证",
      "item": [
        {
          "name": "登录",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"test\",\n  \"password\": \"password\"\n}"
            },
            "url": "{{base_url}}/auth/login"
          }
        }
      ]
    }
  ]
}
```

---

### 26. 部署文档

创建 `docs/DEPLOYMENT.md`:

```markdown
# 生产环境部署指南

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ 磁盘空间

## 部署步骤

### 1. 准备环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置所有必需的变量
```

### 2. 构建镜像

```bash
docker-compose build
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 检查健康状态

```bash
curl http://localhost:8000/health
```

### 5. 配置反向代理 (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

## 监控

- 健康检查: http://localhost:8000/health
- 日志: `docker-compose logs -f`
- 指标: http://localhost:8000/metrics

## 备份

- 数据库: `./data/picturebook.db`
- 上传文件: `./uploads`
- 生成文件: `./outputs`
```

---

## 🎯 优化优先级建议

### 立即处理（本周）

| 优先级 | 项目 | 工作量 | 影响 |
|-------|------|--------|------|
| 🔴 P0 | 移除硬编码API密钥 | 1小时 | 安全 |
| 🔴 P0 | 修复CORS配置 | 30分钟 | 安全 |
| 🔴 P0 | 添加用户认证 | 1天 | 安全 |
| 🟠 P1 | 统一错误处理 | 2小时 | 用户体验 |
| 🟠 P1 | 添加日志轮转 | 1小时 | 可维护性 |

### 短期处理（本月）

| 优先级 | 项目 | 工作量 | 影响 |
|-------|------|--------|------|
| 🟠 P1 | 实现任务队列 | 2天 | 性能 |
| 🟠 P1 | 添加API限流 | 4小时 | 安全 |
| 🟡 P2 | 优化WebSocket | 4小时 | 用户体验 |
| 🟡 P2 | 图片懒加载 | 2小时 | 性能 |
| 🟡 P2 | 添加测试 | 3天 | 质量 |

### 长期规划（季度）

| 优先级 | 项目 | 工作量 | 影响 |
|-------|------|--------|------|
| 🟡 P2 | 完善监控 | 1周 | 可维护性 |
| 🟢 P3 | 代码分割 | 1天 | 性能 |
| 🟢 P3 | CDN集成 | 2天 | 性能 |
| 🟢 P3 | 文档完善 | 1周 | 可维护性 |

---

## 📈 预期效果

实施这些优化后，预期可以达到：

### 安全性
- ✅ 消除所有严重安全漏洞
- ✅ 通过安全审计
- ✅ 符合OWASP标准

### 性能
- ✅ API响应时间减少50%
- ✅ 页面加载速度提升30%
- ✅ 支持10倍并发用户

### 可维护性
- ✅ 代码测试覆盖率达到80%+
- ✅ 平均修复时间（MTTR）减少50%
- ✅ 新功能开发效率提升30%

### 用户体验
- ✅ 错误率降低90%
- ✅ 用户满意度提升
- ✅ 支持更多并发用户

---

## 📚 参考资料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [React性能优化](https://react.dev/learn/render-and-commit)
- [Docker安全](https://docs.docker.com/engine/security/)

---

**文档维护**: 请在每次重大更新后同步更新此文档
**反馈渠道**: [GitHub Issues](https://github.com/your-repo/issues)
