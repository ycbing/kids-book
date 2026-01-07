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
    
    # AI服务配置
    OPENAI_API_KEY: Optional[str] = "sk-lrblpprkvitjenoutducitdhqogfhsfyiziwqvovwftfrfym"
    OPENAI_BASE_URL: str = "https://api.siliconflow.cn/v1"
    OPENAI_MODEL: str = "tencent/Hunyuan-MT-7B"
    
    # 图像生成配置
    IMAGE_MODEL: str = "THUDM/GLM-Z1-9B-0414"
    IMAGE_SIZE: str = "1024x1024"
    
    # 存储配置
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    
    # Redis配置（用于任务队列）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()
