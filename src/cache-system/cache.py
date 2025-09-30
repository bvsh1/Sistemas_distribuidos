from enum import Enum
from typing import Any, Optional, Dict, List
import time
import logging

logger = logging.getLogger(__name__)

class CachePolicy(Enum):
    LRU = "LRU"
    LFU = "LFU" 
    FIFO = "FIFO"

class CacheItem:
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.accessed_at = time.time()
        self.access_count = 0

class Cache:
    def __init__(self, max_size: int = 100, policy: CachePolicy = CachePolicy.LRU):
        self.max_size = max_size
        self.policy = policy
        self.cache: Dict[str, CacheItem] = {}
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            item.accessed_at = time.time()
            item.access_count += 1
            self.hits += 1
            logger.debug(f"Cache hit for key: {key}")
            return item.value
        
        self.misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache[key].value = value
            self.cache[key].accessed_at = time.time()
            self.cache[key].access_count += 1
            return
        
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = CacheItem(key, value)
        logger.debug(f"Added to cache: {key}")
    
    def _evict(self) -> None:
        if not self.cache:
            return
            
        if self.policy == CachePolicy.LRU:
            key_to_remove = min(self.cache.keys(), 
                              key=lambda k: self.cache[k].accessed_at)
        elif self.policy == CachePolicy.LFU:
            key_to_remove = min(self.cache.keys(),
                              key=lambda k: self.cache[k].access_count)
        elif self.policy == CachePolicy.FIFO:
            key_to_remove = min(self.cache.keys(),
                              key=lambda k: self.cache[k].created_at)
        else:
            key_to_remove = min(self.cache.keys(),
                              key=lambda k: self.cache[k].accessed_at)
        
        removed_item = self.cache.pop(key_to_remove)
        logger.debug(f"Evicted from cache: {key_to_remove}")
    
    def clear(self) -> None:
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'policy': self.policy.value,
            'max_size': self.max_size,
            'current_size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 4),
            'total_requests': total_requests
        }
    
    def get_items(self) -> List[Dict[str, Any]]:
        items = []
        for key, item in self.cache.items():
            items.append({
                'key': key[:50] + '...' if len(key) > 50 else key,
                'value_length': len(str(item.value)),
                'created_at': item.created_at,
                'accessed_at': item.accessed_at,
                'access_count': item.access_count
            })
        return items