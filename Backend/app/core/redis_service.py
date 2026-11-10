import json
import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.ttl = settings.ARRIVAL_CACHE_TTL_SECONDS
        self._redis_client = None
        self._memory_cache: dict[str, tuple[float, str]] = {}
        self._is_redis_disabled = False

    async def _get_redis(self):
        if self._is_redis_disabled:
            return None
        if self._redis_client is None and settings.REDIS_URL:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=1.5,
                )
                await self._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis 연결 실패. In-Memory 캐시로 전환합니다: {e}")
                self._redis_client = None
                self._is_redis_disabled = True
        return self._redis_client

    async def get(self, key: str) -> dict | None:
        client = await self._get_redis()
        if client is not None:
            try:
                raw_data = await client.get(key)
                if raw_data:
                    return json.loads(raw_data)
            except Exception as e:
                logger.warning(f"Redis get 실패 ({key}): {e}")
                self._is_redis_disabled = True

        # In-Memory Fallback
        if key in self._memory_cache:
            expires_at, raw_json = self._memory_cache[key]
            if time.time() < expires_at:
                return json.loads(raw_json)
            else:
                del self._memory_cache[key]
        return None

    async def set(self, key: str, value: dict, ttl: int | None = None) -> None:
        expire_seconds = ttl if ttl is not None else self.ttl
        json_str = json.dumps(value, ensure_ascii=False)

        client = await self._get_redis()
        if client is not None:
            try:
                await client.set(key, json_str, ex=expire_seconds)
            except Exception as e:
                logger.warning(f"Redis set 실패 ({key}): {e}")
                self._is_redis_disabled = True

        # In-Memory Fallback 저장 (항상 저장하여 redis 실패 시에도 사용)
        self._memory_cache[key] = (time.time() + expire_seconds, json_str)

cache_service = CacheService()
