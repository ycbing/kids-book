# backend/app/services/retry_helper.py
import asyncio
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional
import httpx

logger = logging.getLogger(__name__)

class APICallError(Exception):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

def retry_on_failure(
    max_retries: int = 3,
    delay: int = 2,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子，每次重试延迟时间 = delay * (backoff_factor ^ attempt)
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.warning(f"⚠️  第 {attempt} 次重试 {func.__name__}...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor

                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✅ 重试成功! (尝试次数: {attempt + 1})")
                    return result

                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"❌ {func.__name__} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                    else:
                        logger.error(f"❌ {func.__name__} 在 {max_retries} 次重试后仍然失败")

            # 所有重试都失败后抛出最后的异常
            raise last_exception

        return wrapper
    return decorator

def handle_api_error(response_text: str, status_code: Optional[int] = None) -> str:
    """
    处理API错误响应

    Args:
        response_text: 响应文本
        status_code: 状态码

    Returns:
        格式化的错误消息
    """
    if "rate limit" in response_text.lower() or "too many requests" in response_text.lower():
        return "API请求频率超限，请稍后再试"
    elif "quota" in response_text.lower() or "limit" in response_text.lower():
        return "API配额已用完，请检查账户余额"
    elif "invalid" in response_text.lower() and "key" in response_text.lower():
        return "API密钥无效，请检查配置"
    elif "timeout" in response_text.lower():
        return "API请求超时，请稍后重试"
    elif "connection" in response_text.lower():
        return "无法连接到API服务器，请检查网络"
    else:
        return f"API错误: {response_text[:200]}"

async def test_api_connection(base_url: str, api_key: str, timeout: int = 10) -> bool:
    """
    测试API连接是否正常

    Args:
        base_url: API基础URL
        api_key: API密钥
        timeout: 超时时间（秒）

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if response.status_code == 200:
                logger.info(f"✅ API连接测试成功: {base_url}")
                return True
            else:
                logger.warning(f"⚠️  API连接测试失败: {base_url} (状态码: {response.status_code})")
                return False
    except Exception as e:
        logger.error(f"❌ API连接测试异常: {base_url} - {str(e)}")
        return False

class APIClientWithFallback:
    """带备用地址的API客户端"""

    def __init__(
        self,
        primary_url: str,
        backup_url: Optional[str] = None,
        api_key: str = "",
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        self.primary_url = primary_url
        self.backup_url = backup_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.current_url = primary_url
        self.use_backup = False

    async def switch_to_backup(self):
        """切换到备用API地址"""
        if self.backup_url and not self.use_backup:
            logger.warning(f"🔄 切换到备用API地址: {self.backup_url}")
            self.current_url = self.backup_url
            self.use_backup = True
            return True
        return False

    async def switch_to_primary(self):
        """切换回主API地址"""
        if self.use_backup:
            logger.info(f"🔄 切换回主API地址: {self.primary_url}")
            self.current_url = self.primary_url
            self.use_backup = False
            return True
        return False

    async def get_current_url(self) -> str:
        """获取当前使用的API地址"""
        return self.current_url
