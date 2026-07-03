"""
Idempotency Utilities for API Write Endpoints
Prevents duplicate logs/requests from being processed twice.
"""
from typing import Optional, Any, Dict
from fastapi import Header, HTTPException
from .cache import local_cache


class IdempotencyManager:
    """
    Manages API write idempotency keys using cache.
    """
    @staticmethod
    def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
        if not key:
            return None
        return local_cache.get(f"idempotency:{key}")

    @staticmethod
    def save_response(key: str, response_data: Dict[str, Any], ttl_seconds: int = 86400) -> None:
        if not key:
            return
        local_cache.set(f"idempotency:{key}", response_data, ttl_seconds)
