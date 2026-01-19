# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI绘本创作平台"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./picturebook.db"

    # 文本生成服务配置
    TEXT_API_KEY: Optional[str] = None
    TEXT_BASE_URL: str = "https://api.siliconflow.cn/v1"
    TEXT_MODEL: str = "THUDM/GLM-4.1V-9B-Thinking"

    # 图像生成服务配置
    IMAGE_API_KEY: Optional[str] = None
    IMAGE_BASE_URL: str = "https://api.siliconflow.cn/v1"
    IMAGE_MODEL: str = "Qwen/Qwen-Image"
    IMAGE_SIZE: str = "1024x1024"

    # 兼容旧配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.siliconflow.cn/v1"
    OPENAI_MODEL: str = "tencent/Hunyuan-MT-7B"

    # API调用配置
    API_TIMEOUT: int = 120
    API_MAX_RETRIES: int = 3
    API_RETRY_DELAY: int = 2
    API_ENABLE_FALLBACK: bool = True

    # 存储配置
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"

    # Redis配置（用于任务队列）
    REDIS_URL: str = "redis://localhost:6379/0"

    # 安全配置
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    JWT_SECRET_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
