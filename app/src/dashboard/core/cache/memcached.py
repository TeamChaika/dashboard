from typing import Optional, Any
import logging

from pymemcache.client.base import Client as MemcachedClient

from .base import BaseCache

logger = logging.getLogger(__name__)


class MemcachedCache(BaseCache):
    def __init__(self, server: str = 'localhost'):
        self._client = MemcachedClient(server, encoding='utf-8')

    def get(self, key: str) -> Optional[Any]:
        try:
            return self._client.get(key)
        except (ConnectionRefusedError, OSError, Exception) as e:
            logger.warning(f"Memcached get failed for key '{key}': {e}. Returning None.")
            return None

    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        try:
            self._client.set(key, value, ttl)
        except (ConnectionRefusedError, OSError, Exception) as e:
            logger.warning(f"Memcached set failed for key '{key}': {e}. Ignoring.")
