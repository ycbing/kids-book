# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
import uuid
from datetime import datetime

from app.config import settings
from app.api.routes import router
from app.api.auth import router as auth_router
from app.models.database import Base, engine
from app.core.exceptions import AppException
from app.core.logging import setup_logging, request_logger, error_logger

# 配置结构化日志系统
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("="*60)
    logger.info("AI绘本创作平台 - 后端服务启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    Base.metadata.create_all(bind=engine)

    yield

    # 关闭时执行
    logger.info("="*60)
    logger.info("后端服务关闭")
    logger.info("="*60)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI驱动的儿童绘本创作平台",
    version="1.0.0",
    lifespan=lifespan
)

# 请求日志中间件 - 添加请求ID追踪
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件 - 为每个请求生成唯一ID并记录详细信息
    """
    # 生成唯一的请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 获取用户ID（如果有）
    user_id = getattr(request.state, "user_id", None)

    # 记录请求开始时间
    start_time = datetime.now()

    # 处理请求
    try:
        response = await call_next(request)

        # 计算处理时间
        process_time = (datetime.now() - start_time).total_seconds()

        # 记录请求日志（使用结构化日志）
        request_logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time,
            client_ip=request.client.host if request.client else None,
            user_id=user_id,
            request_id=request_id
        )

        # 添加请求ID和处理时间到响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        # 计算处理时间
        process_time = (datetime.now() - start_time).total_seconds()

        # 记录错误
        error_logger.log_error(
            error=e,
            context={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration": process_time,
                "client_ip": request.client.host if request.client else None
            }
        )
        raise

# CORS配置 - 安全的跨域资源共享设置
# 从环境变量读取允许的域名，防止CSRF攻击
allowed_origins = settings.allowed_origins_list

if not allowed_origins:
    logger.warning(
        "⚠️  ALLOWED_ORIGINS 未配置！"
    )
    logger.warning(
        "CORS将使用严格模式，仅允许相同源访问。"
    )
    logger.warning(
        "请在 .env 文件中设置 ALLOWED_ORIGINS 环境变量。"
    )
    logger.warning(
        "示例: ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com"
    )
else:
    logger.info(f"✅ CORS允许的域名: {', '.join(allowed_origins)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 从配置读取，而非允许所有域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # 明确允许的方法
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],  # 明确允许的请求头
)

# 创建必要的目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

# ============ 全局异常处理器 ============

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义应用异常"""
    logger.error(
        f"业务异常: {exc.error_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )

    # 构建错误响应
    response_data = exc.to_dict()
    response_data["path"] = request.url.path
    response_data["timestamp"] = datetime.utcnow().isoformat()

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    # 记录详细的错误日志
    logger.error(
        f"未处理的异常: {type(exc).__name__}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_message": str(exc)
        }
    )

    # 生产环境不返回详细错误信息，防止信息泄露
    error_detail = str(exc) if settings.DEBUG else "服务器内部错误"

    response_data = {
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": error_detail
        },
        "path": request.url.path,
        "timestamp": datetime.utcnow().isoformat()
    }

    # 开发环境添加额外信息
    if settings.DEBUG:
        response_data["error"]["type"] = type(exc).__name__
        response_data["debug"] = True

    return JSONResponse(
        status_code=500,
        content=response_data
    )

# 注册路由
app.include_router(auth_router, prefix=settings.API_PREFIX)  # 认证路由
app.include_router(router, prefix=settings.API_PREFIX)  # 业务路由

@app.get("/")
async def root():
    return {
        "message": "欢迎使用AI绘本创作平台",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
