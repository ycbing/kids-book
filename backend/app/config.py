# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI绘本创作平台"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # 数据库配置
    # SQLite: sqlite:///./picturebook.db (开发环境)
    # PostgreSQL: postgresql://user:password@localhost:5432/dbname (生产环境)
    DATABASE_URL: str = "sqlite:///./picturebook.db"

    # 数据库连接池配置（仅PostgreSQL有效）
    DB_POOL_SIZE: int = 5  # 连接池大小
    DB_MAX_OVERFLOW: int = 10  # 最大溢出连接数
    DB_POOL_RECYCLE: int = 3600  # 连接回收时间（秒）
    DB_ECHO: bool = False  # 是否打印SQL语句

    # AI服务配置 - 文本生成（从环境变量读取，不要设置默认值）
    TEXT_API_KEY: Optional[str] = None
    TEXT_BASE_URL: str = "https://api.openai.com/v1"
    TEXT_MODEL: str = "gpt-3.5-turbo"

    # AI服务配置 - 图像生成（从环境变量读取，不要设置默认值）
    IMAGE_API_KEY: Optional[str] = None
    IMAGE_BASE_URL: str = "https://api.openai.com/v1"
    IMAGE_MODEL: str = "dall-e-3"
    IMAGE_SIZE: str = "1024x1024"

    # 兼容旧配置（如果新的配置不存在，使用旧配置）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    # 存储配置
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"

    # CORS安全配置（允许的跨域来源）
    # 开发环境默认允许localhost，生产环境必须显式配置
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # JWT密钥配置（用于用户认证）
    # 生产环境必须设置强密钥
    JWT_SECRET_KEY: Optional[str] = None

    # Redis配置（用于任务队列）
    REDIS_URL: str = "redis://localhost:6379/0"

    # API调用配置（针对第三方中转站）
    API_TIMEOUT: int = 120  # 请求超时时间（秒）
    API_MAX_RETRIES: int = 3  # 最大重试次数
    API_RETRY_DELAY: int = 2  # 重试延迟（秒）
    API_BACKUP_BASE_URL: Optional[str] = None  # 备用API地址
    API_ENABLE_FALLBACK: bool = True  # 是否启用备用地址

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 仅在生产环境或明确要求时验证
        if not self.DEBUG:
            self._validate_required_vars()
        else:
            # 开发环境只给出警告
            self._warn_missing_vars()

    def _validate_required_vars(self):
        """验证必需的环境变量（生产环境）"""
        errors = []

        # 检查文本API配置
        text_api_key = self.TEXT_API_KEY or self.OPENAI_API_KEY
        if not text_api_key:
            errors.append("TEXT_API_KEY 或 OPENAI_API_KEY 未设置")

        # 检查图像API配置
        image_api_key = self.IMAGE_API_KEY or self.OPENAI_API_KEY
        if not image_api_key:
            errors.append("IMAGE_API_KEY 或 OPENAI_API_KEY 未设置")

        if errors:
            error_msg = (
                "配置验证失败 - 缺少必需的环境变量:\n" +
                "\n".join(f"  ❌ {e}" for e in errors) +
                "\n\n请在 .env 文件中配置这些变量。" +
                "\n可以参考 backend/.env.example 文件。"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("✅ 配置验证通过")

    def _warn_missing_vars(self):
        """开发环境只给出警告，不阻止启动"""
        missing = []

        text_api_key = self.TEXT_API_KEY or self.OPENAI_API_KEY
        if not text_api_key:
            missing.append("TEXT_API_KEY")

        image_api_key = self.IMAGE_API_KEY or self.OPENAI_API_KEY
        if not image_api_key:
            missing.append("IMAGE_API_KEY")

        if missing:
            logger.warning(
                "⚠️  开发环境检测到以下环境变量未设置: " +
                ", ".join(missing) +
                "\n请在 backend/.env 文件中配置（参考 backend/.env.example）"
            )

    def get_text_config(self):
        """获取文本生成配置（向后兼容）"""
        api_key = self.TEXT_API_KEY or self.OPENAI_API_KEY
        base_url = self.TEXT_BASE_URL or self.OPENAI_BASE_URL or "https://api.openai.com/v1"
        model = self.TEXT_MODEL
        return api_key, base_url, model

    def get_image_config(self):
        """获取图像生成配置（向后兼容）"""
        api_key = self.IMAGE_API_KEY or self.OPENAI_API_KEY
        base_url = self.IMAGE_BASE_URL or self.OPENAI_BASE_URL or "https://api.openai.com/v1"
        model = self.IMAGE_MODEL
        return api_key, base_url, model

    @property
    def allowed_origins_list(self) -> list:
        """获取CORS允许的域名列表"""
        if not self.ALLOWED_ORIGINS:
            return []

        # 分割并去除空格
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        # 过滤空字符串
        return [origin for origin in origins if origin]

settings = Settings()
