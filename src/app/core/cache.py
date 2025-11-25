import redis.asyncio as redis

from typing import Optional

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class Cache:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client

    async def get(self, key: str) -> Optional[str]:
        try:
            client = await self._get_client()
            value = await client.get(key)
            return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        try:
            client = await self._get_client()
            await client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

_cache_instance = None

def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance