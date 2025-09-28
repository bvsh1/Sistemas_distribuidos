from typing import Any, Optional, Dict
import time
from collections import OrderedDict

class CacheItem:
    def __init__(self, value: Any, timestamp: float = None):
        self.value = value
        self.timestamp = timestamp or time.time()
        self.access_count = 0
        self.last_access = self.timestamp

    def access(self):
        self.access_count += 1
        self.last_access = time.time()
        return self.value

class CachePolicy:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, CacheItem] = {}
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            
            if self.ttl and (time.time() - item.timestamp > self.ttl):
                self.misses += 1
                del self.cache[key]
                return None
                
            self.hits += 1
            return item.access()
        
        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        if self.max_size and len(self.cache) >= self.max_size:
            self.evict()
        
        self.cache[key] = CacheItem(value)
    
    def evict(self) -> None:
        raise NotImplementedError("Subclasses must implement evict method")
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl
        }

class LRUCache(CachePolicy):
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        super().__init__(max_size, ttl)
        self.access_order = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        item = super().get(key)
        if item is not None:
            self.access_order.move_to_end(key)
        return item
    
    def set(self, key: str, value: Any) -> None:
        super().set(key, value)
        self.access_order[key] = True
        self.access_order.move_to_end(key)
    
    def evict(self) -> None:
        if self.access_order:
            oldest_key = next(iter(self.access_order))
            del self.cache[oldest_key]
            del self.access_order[oldest_key]

class LFUCache(CachePolicy):
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        super().__init__(max_size, ttl)
        self.freq_map = {}
    
    def get(self, key: str) -> Optional[Any]:
        item = super().get(key)
        if item is not None and key in self.freq_map:
            self.freq_map[key] += 1
        return item
    
    def set(self, key: str, value: Any) -> None:
        super().set(key, value)
        self.freq_map[key] = 1
    
    def evict(self) -> None:
        if self.freq_map:
            min_freq = min(self.freq_map.values())
            candidates = [k for k, v in self.freq_map.items() if v == min_freq]
            
            if candidates:
                victim_key = candidates[0]
                del self.cache[victim_key]
                del self.freq_map[victim_key]

class FIFOCache(CachePolicy):
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        super().__init__(max_size, ttl)
        self.queue = []
    
    def set(self, key: str, value: Any) -> None:
        super().set(key, value)
        self.queue.append(key)
    
    def evict(self) -> None:
        if self.queue:
            oldest_key = self.queue.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]

class CacheFactory:
    @staticmethod
    def create_cache(policy: str = 'lru', **kwargs) -> CachePolicy:
        policy = policy.lower()
        if policy == 'lru':
            return LRUCache(**kwargs)
        elif policy == 'lfu':
            return LFUCache(**kwargs)
        elif policy == 'fifo':
            return FIFOCache(**kwargs)
        else:
            raise ValueError(f"Política de caché no soportada: {policy}")