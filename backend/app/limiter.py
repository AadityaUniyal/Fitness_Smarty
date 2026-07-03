"""
Token-Bucket Rate Limiter with Redis support and local fallback.
"""
import time
import os
from typing import Tuple
from slowapi import Limiter
from slowapi.util import get_remote_address

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TokenBucketLimiter:
    """
    Distributed Token-Bucket rate limiter shared across replicas.
    """
    def __init__(self, redis_url: str):
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, socket_timeout=1.0)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
        
        # Local fallback store: {key: (tokens, last_updated_time)}
        self.local_store = {}

    def is_allowed(self, key: str, rate: float, capacity: float) -> Tuple[bool, float]:
        """
        Check if a request is allowed under the rate limit.
        rate: tokens added per second
        capacity: maximum burst capacity
        
        Returns: (is_allowed: bool, remaining_tokens: float)
        """
        now = time.time()
        
        if self.redis_client:
            try:
                # Key names in Redis
                tokens_key = f"limiter:{key}:tokens"
                updated_key = f"limiter:{key}:updated"
                
                # Fetch current values
                pipe = self.redis_client.pipeline()
                pipe.get(tokens_key)
                pipe.get(updated_key)
                tokens_val, updated_val = pipe.execute()
                
                if tokens_val is not None and updated_val is not None:
                    last_tokens = float(tokens_val)
                    last_updated = float(updated_val)
                    # Compute refilled tokens
                    elapsed = now - last_updated
                    tokens = min(capacity, last_tokens + elapsed * rate)
                else:
                    tokens = capacity
                
                if tokens >= 1.0:
                    tokens -= 1.0
                    allowed = True
                else:
                    allowed = False
                
                # Save back to Redis
                pipe = self.redis_client.pipeline()
                pipe.set(tokens_key, tokens)
                pipe.set(updated_key, now)
                # Keep keys alive for an hour
                pipe.expire(tokens_key, 3600)
                pipe.expire(updated_key, 3600)
                pipe.execute()
                
                return allowed, tokens
                
            except Exception as e:
                print(f"[!] Redis rate limiter error: {e}. Using local fallback.")

        # Local memory fallback
        last_tokens, last_updated = self.local_store.get(key, (capacity, now))
        elapsed = now - last_updated
        tokens = min(capacity, last_tokens + elapsed * rate)
        
        if tokens >= 1.0:
            tokens -= 1.0
            allowed = True
        else:
            allowed = False
            
        self.local_store[key] = (tokens, now)
        return allowed, tokens


# Redis configurations
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
token_bucket_limiter = TokenBucketLimiter(redis_url)

# SlowAPI Limiter instance for legacy endpoint routing
limiter = Limiter(key_func=get_remote_address)
