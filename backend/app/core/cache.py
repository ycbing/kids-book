# backend/app/core/cache.py
"""
缓存层实现

支持：
- Redis缓存
- 内存缓存（fallback）
- 缓存装饰器
- 缓存失效策略
"""

import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Callable, TypeVar, Union
from functools import wraps
from datetime import timedelta
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend:
    """缓存后端基类"""

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        raise NotImplementedError

    async def clear(self, pattern: str = None) -> int:
        """清空缓存"""
        raise NotImplementedError


class RedisCache(CacheBackend):
    """Redis缓存后端"""

    def __init__(self):
        self.redis = None
        self._initialized = False

    async def _get_redis(self):
        """延迟初始化Redis连接"""
        if not self._initialized:
            try:
                import redis.asyncio as aioredis
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                self._initialized = True
                logger.info("✅ Redis缓存已启用")
            except Exception as e:
                logger.warning(f"⚠️  Redis连接失败: {str(e)}，使用内存缓存")
                self.redis = None
                self._initialized = True

        return self.redis

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        redis = await self._get_redis()
        if not redis:
            return None

        try:
            data = await redis.get(key)
            if data:
                # 尝试JSON解析
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    # 尝试pickle解析
                    try:
                        return pickle.loads(data.encode())
                    except:
                        return data
            return None
        except Exception as e:
            logger.error(f"Redis GET失败: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            # 尝试JSON序列化
            try:
                data = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # 使用pickle序列化
                data = pickle.dumps(value).decode('latin1')

            await redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis SET失败: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE失败: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        redis = await self._get_redis()
        if not redis:
            return False

        try:
            return await redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS失败: {str(e)}")
            return False

    async def clear(self, pattern: str = None) -> int:
        """清空缓存"""
        redis = await self._get_redis()
        if not redis:
            return 0

        try:
            if pattern:
                keys = await redis.keys(pattern)
                if keys:
                    return await redis.delete(*keys)
            else:
                await redis.flushdb()
                return 1
        except Exception as e:
            logger.error(f"Redis CLEAR失败: {str(e)}")
            return 0


class MemoryCache(CacheBackend):
    """内存缓存后端（fallback）"""

    def __init__(self):
        self.cache: dict = {}
        self.ttls: dict = {}

    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self.ttls:
            return False

        import time
        return time.time() > self.ttls[key]

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache and not self._is_expired(key):
            return self.cache.get(key)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        import time
        self.cache[key] = value
        self.ttls[key] = time.time() + ttl
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            del self.ttls[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self.cache and not self._is_expired(key)

    async def clear(self, pattern: str = None) -> int:
        """清空缓存"""
        if pattern:
            import fnmatch
            keys_to_delete = [
                k for k in self.cache.keys()
                if fnmatch.fnmatch(k, pattern) and not self._is_expired(k)
            ]
            for key in keys_to_delete:
                del self.cache[key]
                del self.ttls[key]
            return len(keys_to_delete)
        else:
            count = len(self.cache)
            self.cache.clear()
            self.ttls.clear()
            return count


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.backend: Optional[CacheBackend] = None
        self._initialized = False

    async def initialize(self):
        """初始化缓存后端"""
        if not self._initialized:
            if settings.REDIS_URL:
                self.backend = RedisCache()
            else:
                logger.info("ℹ️  Redis未配置，使用内存缓存")
                self.backend = MemoryCache()
            self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        await self.initialize()
        return await self.backend.get(key) if self.backend else None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        await self.initialize()
        return await self.backend.set(key, value, ttl) if self.backend else False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        await self.initialize()
        return await self.backend.delete(key) if self.backend else False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        await self.initialize()
        return await self.backend.exists(key) if self.backend else False

    async def clear(self, pattern: str = None) -> int:
        """清空缓存"""
        await self.initialize()
        return await self.backend.clear(pattern) if self.backend else 0


# 全局缓存管理器实例
cache_manager = CacheManager()


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    生成缓存键

    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        缓存键
    """
    # 序列化参数
    args_str = json.dumps(args, default=str, sort_keys=True)
    kwargs_str = json.dumps(kwargs, default=str, sort_keys=True)

    # 生成哈希
    key_content = f"{func_name}:{args_str}:{kwargs_str}"
    key_hash = hashlib.md5(key_content.encode()).hexdigest()

    return f"cache:{key_hash}"


def cached(ttl: int = 300, key_prefix: str = None):
    """
    缓存装饰器

    Args:
        ttl: 缓存时间（秒），默认5分钟
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=600)
        async def get_user_books(user_id: int):
            # ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, args, kwargs)

            # 尝试从缓存获取
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            logger.debug(f"缓存未命中: {cache_key}")
            result = await func(*args, **kwargs)

            # 存入缓存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """
    缓存失效装饰器

    Args:
        pattern: 缓存键模式

    Usage:
        @cache_invalidate("user:*")
        async def update_user(user_id: int, data: dict):
            # 更新后失效缓存
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 执行函数
            result = await func(*args, **kwargs)

            # 失效缓存
            await cache_manager.clear(pattern)

            return result

        return wrapper
    return decorator


# 专用缓存函数
async def cache_get_book(book_id: int) -> Optional[Any]:
    """获取缓存的绘本"""
    cache_key = f"book:{book_id}"
    return await cache_manager.get(cache_key)


async def cache_set_book(book_id: int, book: Any, ttl: int = 600):
    """设置绘本缓存"""
    cache_key = f"book:{book_id}"
    await cache_manager.set(cache_key, book, ttl)


async def cache_delete_book(book_id: int):
    """删除绘本缓存"""
    cache_key = f"book:{book_id}"
    await cache_manager.delete(cache_key)


async def cache_get_user_books(user_id: int) -> Optional[Any]:
    """获取缓存的用户绘本列表"""
    cache_key = f"user_books:{user_id}"
    return await cache_manager.get(cache_key)


async def cache_set_user_books(user_id: int, books: Any, ttl: int = 300):
    """设置用户绘本列表缓存"""
    cache_key = f"user_books:{user_id}"
    await cache_manager.set(cache_key, books, ttl)


async def cache_invalidate_user(user_id: int):
    """失效用户相关缓存"""
    await cache_manager.clear(f"user_books:{user_id}*")
