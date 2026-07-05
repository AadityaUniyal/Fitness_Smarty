import pytest
import time
from app.cache import RedisCacheWrapper
from app.limiter import TokenBucketLimiter


def test_cache_fallback():
    # Test local memory fallback of Redis cache wrapper
    cache = RedisCacheWrapper("redis://localhost:9999/0")  # Invalid URL to trigger fallback
    
    cache.set("test_key", {"data": 123}, ttl_seconds=2)
    assert cache.get("test_key") == {"data": 123}
    
    # Check expiration
    time.sleep(2.5)
    assert cache.get("test_key") is None


def test_token_bucket_limiter():
    limiter = TokenBucketLimiter("redis://localhost:9999/0")  # Fallback to local
    
    # Allowed requests within capacity (rate=1, capacity=3)
    allowed, tokens = limiter.is_allowed("user_123", rate=1.0, capacity=3.0)
    assert allowed
    assert tokens <= 2.05
    
    allowed, tokens = limiter.is_allowed("user_123", rate=1.0, capacity=3.0)
    assert allowed
    assert tokens <= 1.05
    
    allowed, tokens = limiter.is_allowed("user_123", rate=1.0, capacity=3.0)
    assert allowed
    
    # Should block since bucket is now empty
    allowed, tokens = limiter.is_allowed("user_123", rate=1.0, capacity=3.0)
    assert not allowed
