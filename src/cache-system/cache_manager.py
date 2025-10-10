import time
from collections import OrderedDict, defaultdict
import logging
from typing import Optional, Any

class LRUCache:
    """Implementación de caché con política LRU"""
    def __init__(self, capacity: int, ttl: Optional[int] = None):
        self.capacity = capacity
        self.ttl = ttl
        self.cache = OrderedDict()
        self.access_times = {}
    
    def get(self, key: int) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        if self.ttl and time.time() - self.access_times[key] > self.ttl:
            self._remove(key)
            return None
        
        self.cache.move_to_end(key)
        self.access_times[key] = time.time()
        return self.cache[key]
    
    def put(self, key: int, value: Any) -> None:
        if key in self.cache:
            self.cache[key] = value
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                oldest_key = next(iter(self.cache))
                self._remove(oldest_key)
            self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _remove(self, key: int) -> None:
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
    
    def size(self) -> int:
        return len(self.cache)

class CacheManager:
    """Gestor principal de caché"""
    def __init__(self, policy: str = 'LRU', capacity: int = 1000, ttl: Optional[int] = None):
        self.policy = policy.upper()
        self.capacity = capacity
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(__name__)
        
        if self.policy == 'LRU':
            self.cache = LRUCache(capacity, ttl)
        else:
            raise ValueError(f"Política no soportada: {policy}")
        
        self.logger.info(f"Caché inicializada - Política: {policy}, Capacidad: {capacity}")
    
    def get(self, key: int) -> Optional[Any]:
        result = self.cache.get(key)
        if result is not None:
            self.hits += 1
        else:
            self.misses += 1
        return result
    
    def put(self, key: int, value: Any) -> None:
        self.cache.put(key, value)
    
    def get_stats(self) -> dict:
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        miss_rate = self.misses / total_requests if total_requests > 0 else 0
        
        return {
            'policy': self.policy,
            'capacity': self.capacity,
            'current_size': self.cache.size(),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 4),
            'miss_rate': round(miss_rate, 4),
            'total_requests': total_requests
        }
    
    def reset_stats(self) -> None:
        self.hits = 0
        self.misses = 0