# backend/app/core/validator.py
"""
环境变量和配置验证工具
"""

import os
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message: str, errors: List[str] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class ConfigValidator:
    """配置验证器"""

    def __init__(self, settings):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []

    async def validate_all(self, skip_connection_tests: bool = False) -> bool:
        """
        执行所有验证

        Args:
            skip_connection_tests: 是否跳过连接测试（开发环境可能需要）

        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()

        logger.info("🔍 开始配置验证...")

        # 1. 验证必需的环境变量
        self._validate_required_vars()

        # 2. 验证URL格式
        self._validate_urls()

        # 3. 验证数值范围
        self._validate_numeric_ranges()

        # 4. 验证路径
        self._validate_paths()

        # 5. 验证JWT配置
        self._validate_jwt_config()

        # 如果有错误，提前返回
        if self.errors:
            return False

        # 6. 测试连接（可选）
        if not skip_connection_tests:
            await self._test_connections()

        # 7. 打印警告
        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"⚠️  {warning}")

        # 8. 打印结果
        if self.errors:
            self._print_validation_result(False)
            return False
        else:
            self._print_validation_result(True)
            return True

    def _validate_required_vars(self):
        """验证必需的环境变量"""
        logger.info("  📋 验证必需的环境变量...")

        required_vars = {
            "数据库": ["DATABASE_URL"],
        }

        # 生产环境必需的变量
        if not self.settings.DEBUG:
            required_vars["生产环境"] = [
                "JWT_SECRET_KEY",
            ]

        # 检查API密钥（至少需要一个）
        text_api_key = self.settings.TEXT_API_KEY or self.settings.OPENAI_API_KEY
        image_api_key = self.settings.IMAGE_API_KEY or self.settings.OPENAI_API_KEY

        if not text_api_key:
            self.errors.append("TEXT_API_KEY 或 OPENAI_API_KEY 未设置（文本生成必需）")

        if not image_api_key:
            self.errors.append("IMAGE_API_KEY 或 OPENAI_API_KEY 未设置（图像生成必需）")

        # 检查其他必需变量
        for category, vars in required_vars.items():
            for var in vars:
                value = getattr(self.settings, var, None)
                if not value:
                    self.errors.append(f"{var} 未设置（{category}）")

    def _validate_urls(self):
        """验证URL格式"""
        logger.info("  🌐 验证URL格式...")

        urls_to_validate = {
            "DATABASE_URL": self.settings.DATABASE_URL,
            "TEXT_BASE_URL": self.settings.TEXT_BASE_URL,
            "IMAGE_BASE_URL": self.settings.IMAGE_BASE_URL,
            "REDIS_URL": self.settings.REDIS_URL,
        }

        for name, url in urls_to_validate.items():
            if url:
                try:
                    parsed = urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        self.errors.append(f"{name} 格式无效: {url}")

                    # 检查支持的协议
                    if name == "DATABASE_URL":
                        if parsed.scheme not in ["sqlite", "postgresql", "mysql"]:
                            self.errors.append(
                                f"{name} 不支持的协议: {parsed.scheme}"
                            )
                    elif name in ["TEXT_BASE_URL", "IMAGE_BASE_URL"]:
                        if parsed.scheme not in ["http", "https"]:
                            self.errors.append(
                                f"{name} 必须使用http或https协议"
                            )

                except Exception as e:
                    self.errors.append(f"{name} 解析失败: {str(e)}")

    def _validate_numeric_ranges(self):
        """验证数值范围"""
        logger.info("  🔢 验证数值范围...")

        numeric_validations = {
            "API_TIMEOUT": (self.settings.API_TIMEOUT, 1, 600),
            "API_MAX_RETRIES": (self.settings.API_MAX_RETRIES, 0, 10),
            "API_RETRY_DELAY": (self.settings.API_RETRY_DELAY, 0, 60),
            "DB_POOL_SIZE": (self.settings.DB_POOL_SIZE, 1, 100),
            "DB_MAX_OVERFLOW": (self.settings.DB_MAX_OVERFLOW, 0, 100),
        }

        for name, (value, min_val, max_val) in numeric_validations.items():
            if value < min_val or value > max_val:
                self.errors.append(
                    f"{name}={value} 超出范围 [{min_val}, {max_val}]"
                )

    def _validate_paths(self):
        """验证路径配置"""
        logger.info("  📁 验证路径配置...")

        paths = {
            "UPLOAD_DIR": self.settings.UPLOAD_DIR,
            "OUTPUT_DIR": self.settings.OUTPUT_DIR,
        }

        for name, path in paths.items():
            # 检查路径是否为绝对路径或相对路径
            if not path or path == "/":
                self.errors.append(f"{name} 路径配置无效: {path}")
                continue

            # 如果是相对路径，尝试创建
            if not os.path.isabs(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"    ✅ 创建目录: {path}")
                except Exception as e:
                    self.errors.append(f"{name} 无法创建目录 {path}: {str(e)}")

    def _validate_jwt_config(self):
        """验证JWT配置"""
        logger.info("  🔐 验证JWT配置...")

        if not self.settings.JWT_SECRET_KEY:
            if not self.settings.DEBUG:
                self.errors.append(
                    "JWT_SECRET_KEY 未设置（生产环境必须设置强密钥）"
                )
            else:
                self.warnings.append(
                    "JWT_SECRET_KEY 未设置（开发环境使用默认密钥，不安全！）"
                )
        else:
            # 检查密钥强度
            secret_key = self.settings.JWT_SECRET_KEY
            if len(secret_key) < 32:
                self.warnings.append(
                    f"JWT_SECRET_KEY 长度不足（当前: {len(secret_key)}，建议: 32+）"
                )

            # 检查是否使用弱密钥
            weak_keys = ["secret", "password", "key", "test", "demo"]
            if any(weak_key in secret_key.lower() for weak_key in weak_keys):
                self.errors.append(
                    "JWT_SECRET_KEY 使用了弱密钥，请使用强随机字符串"
                )

    async def _test_connections(self):
        """测试外部服务连接"""
        logger.info("  🔗 测试外部服务连接...")

        # 测试数据库连接
        await self._test_database_connection()

        # 测试API连接
        await self._test_api_connections()

        # 测试Redis连接（如果配置了）
        if self.settings.REDIS_URL:
            await self._test_redis_connection()

    async def _test_database_connection(self):
        """测试数据库连接"""
        logger.info("    🗄️  测试数据库连接...")

        try:
            from app.models.database import engine, SessionLocal

            # 测试连接
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()

            logger.info("    ✅ 数据库连接成功")

        except Exception as e:
            self.errors.append(f"数据库连接失败: {str(e)}")

    async def _test_api_connections(self):
        """测试API连接"""
        logger.info("    🤖 测试AI服务API连接...")

        # 获取API配置
        text_api_key, text_base_url, _ = self.settings.get_text_config()
        image_api_key, image_base_url, _ = self.settings.get_image_config()

        # 测试文本API
        if text_api_key:
            success = await self._test_api_endpoint(
                "文本生成API",
                text_base_url,
                text_api_key,
                "/models"
            )

            if not success:
                self.errors.append("文本生成API连接失败")
        else:
            logger.warning("    ⚠️  文本API密钥未配置，跳过连接测试")

        # 测试图像API
        if image_api_key:
            success = await self._test_api_endpoint(
                "图像生成API",
                image_base_url,
                image_api_key,
                "/models"
            )

            if not success:
                self.errors.append("图像生成API连接失败")
        else:
            logger.warning("    ⚠️  图像API密钥未配置，跳过连接测试")

    async def _test_api_endpoint(
        self,
        name: str,
        base_url: str,
        api_key: str,
        endpoint: str = "/models"
    ) -> bool:
        """测试API端点"""
        try:
            # 移除末尾斜杠
            base_url = base_url.rstrip("/")

            # 构造完整URL
            url = f"{base_url}{endpoint}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key[:10]}...",  # 只显示部分
                    }
                )

                if response.status_code in [200, 401]:
                    # 200表示成功，401表示密钥格式正确但无效
                    logger.info(f"    ✅ {name} 连接成功")
                    return True
                else:
                    logger.warning(
                        f"    ⚠️  {name} 返回状态码: {response.status_code}"
                    )
                    return response.status_code == 401  # 401也算连接成功

        except httpx.TimeoutException:
            logger.warning(f"    ⚠️  {name} 连接超时")
            return False
        except Exception as e:
            logger.warning(f"    ⚠️  {name} 连接失败: {str(e)}")
            return False

    async def _test_redis_connection(self):
        """测试Redis连接"""
        logger.info("    🔴 测试Redis连接...")

        try:
            import redis

            client = redis.from_url(self.settings.REDIS_URL)
            client.ping()
            client.close()

            logger.info("    ✅ Redis连接成功")

        except Exception as e:
            self.warnings.append(f"Redis连接失败: {str(e)}")

    def _print_validation_result(self, success: bool):
        """打印验证结果"""
        print("\n" + "=" * 60)

        if success:
            print("✅ 配置验证通过！")
            print("=" * 60)

            # 打印配置摘要
            self._print_config_summary()

        else:
            print("❌ 配置验证失败！")
            print("=" * 60)
            print("\n错误列表:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

            print("\n💡 解决方案:")
            print("  1. 检查 .env 文件是否存在")
            print("  2. 参考 .env.example 文件配置所有必需的环境变量")
            print("  3. 确保所有必需的服务正在运行")
            print("  4. 检查网络连接和防火墙设置")

        print("=" * 60 + "\n")

    def _print_config_summary(self):
        """打印配置摘要"""
        print("\n📊 配置摘要:")
        print(f"  环境: {'开发环境' if self.settings.DEBUG else '生产环境'}")
        print(f"  数据库: {self.settings.DATABASE_URL}")
        print(f"  文本API: {self.settings.TEXT_BASE_URL}")
        print(f"  图像API: {self.settings.IMAGE_BASE_URL}")

        if self.settings.REDIS_URL:
            print(f"  Redis: {self.settings.REDIS_URL}")

        print()


async def validate_config(settings, skip_connection_tests: bool = False) -> bool:
    """
    验证配置的便捷函数

    Args:
        settings: Settings实例
        skip_connection_tests: 是否跳过连接测试

    Returns:
        bool: 验证是否通过
    """
    validator = ConfigValidator(settings)
    return await validator.validate_all(skip_connection_tests=skip_connection_tests)
