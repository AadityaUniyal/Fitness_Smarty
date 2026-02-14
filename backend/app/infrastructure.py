"""
Infrastructure & Optimization Utilities

Model caching, batch processing, and performance monitoring
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time


class ModelCache:
    """
    In-memory cache for model predictions
    
    Speeds up repeated queries
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time-to-live for cache entries
        """
        self.cache = {}
        self.ttl = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0
        print(f"✓ Model Cache initialized (TTL: {ttl_seconds}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                self.hit_count += 1
                return entry['value']
            else:
                # Expired
                del self.cache[key]
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set cache value"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
           'total_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': round(hit_rate, 1),
            'ttl_seconds': self.ttl
        }


class BatchProcessor:
    """
    Batch processing for multiple items
    
    Process many items efficiently
    """
    
    def __init__(self):
        """Initialize batch processor"""
        self.processing_times = []
        print("✓ Batch Processor initialized")
    
    def process_batch(
        self,
        items: List[Any],
        process_func: callable
    ) -> List[Dict[str, Any]]:
        """
        Process batch of items
        
        Args:
            items: Items to process
            process_func: Function to apply to each item
            
        Returns:
            List of results
        """
        start_time = time.time()
        
        results = []
        for idx, item in enumerate(items):
            try:
                result = process_func(item)
                results.append({
                    'index': idx,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e)
                })
        
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        return results
    
    def stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self.processing_times:
            return {'total_batches': 0}
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        
        return {
            'total_batches': len(self.processing_times),
            'avg_processing_time_seconds': round(avg_time, 2),
            'total_processing_time_seconds': round(sum(self.processing_times), 2)
        }


class HealthMonitor:
    """
    System health monitoring
    
    Track model performance and system status
    """
    
    def __init__(self):
        """Initialize health monitor"""
        self.start_time = datetime.now()
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        print("✓ Health Monitor initialized")
    
    def record_request(self, endpoint: str):
        """Record API request"""
        self.request_counts[endpoint] += 1
    
    def record_error(self, endpoint: str):
        """Record API error"""
        self.error_counts[endpoint] += 1
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        uptime = datetime.now() - self.start_time
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'status': 'healthy' if error_rate < 5 else 'degraded',
            'uptime_seconds': int(uptime.total_seconds()),
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate_percent': round(error_rate, 2),
            'most_used_endpoints': sorted(
                self.request_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# Singleton instances
_cache_instance: Optional[ModelCache] = None
_batch_processor: Optional[BatchProcessor] = None
_health_monitor: Optional[HealthMonitor] = None

def get_model_cache() -> ModelCache:
    """Get singleton cache"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ModelCache()
    return _cache_instance

def get_batch_processor() -> BatchProcessor:
    """Get singleton batch processor"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor

def get_health_monitor() -> HealthMonitor:
    """Get singleton health monitor"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
