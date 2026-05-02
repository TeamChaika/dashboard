from typing import Optional, Any
from django.core.cache import cache

from .base import BaseCache


class DjangoCacheBackend(BaseCache):
    """Wrapper для Django cache (LocMemCache, Redis, etc.)"""
    
    def __init__(self):
        self._cache = cache
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        self._cache.set(key, value, timeout=ttl if ttl > 0 else None)

