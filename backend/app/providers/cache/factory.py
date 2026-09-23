from app.domain.protocols import Cache
from app.providers.cache.in_memory_cache import InMemoryCache
from app.providers.cache.redis_cache import RedisCache
from app.providers.redis_client import get_redis_url


def get_cache() -> Cache:
    """RedisCache whenever REDIS_URL is set (the default, and required for
    caching to survive horizontal scaling); InMemoryCache as a fallback for
    local dev without Redis running."""
    if get_redis_url():
        return RedisCache()
    return InMemoryCache()
