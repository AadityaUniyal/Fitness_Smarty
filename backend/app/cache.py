"""
Proper Caching System with Redis support and local fallback.
"""
import time
import os
import json
import logging
from typing import Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self.store = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self.store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self.store[key]
            return None
        return entry["value"]

    def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self.store[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def clear(self) -> None:
        self.store.clear()


class RedisCacheWrapper:
    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url, socket_timeout=1.0
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache at %s", redis_url)
            except Exception as e:
                logger.warning(
                    "Redis connection failed: %s. Falling back to in-memory cache.",
                    e,
                )
                self.redis_client = None
        self.fallback = MemoryCache(default_ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val)
                return None
            except Exception as e:
                logger.warning("Redis GET error: %s", e)
                return self.fallback.get(key)
        return self.fallback.get(key)

    def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return
            except Exception as e:
                logger.warning("Redis SETEX error: %s", e)

        self.fallback.set(key, value, ttl_seconds)

    def clear(self) -> None:
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                return
            except Exception as e:
                logger.warning("Redis FLUSHDB error: %s", e)
        self.fallback.clear()


# Global cache instance
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
local_cache = RedisCacheWrapper(redis_url)

