from .memcached import MemcachedCache
from .django_cache import DjangoCacheBackend

# Используем Django cache вместо Memcached для надёжности
memcached_cache = DjangoCacheBackend()  # Было: MemcachedCache()
