import pickle

from redis import Redis

from app.providers.redis_client import get_redis_client


class RedisCache:
    """Cache Protocol implementation backed by Redis. Default cache backend
    whenever REDIS_URL is set (see factory.py) -- shared across however many
    backend instances are running, unlike InMemoryCache.

    Values are pickled: callers hand this cache whatever they like (a
    TriageResult, a (result, str) tuple, a plain stats dict, ...), and every
    value stored here was produced by this process itself, never taken
    verbatim from external/user input -- so unpickling it back carries no
    injection risk, and pickle saves every caller from hand-rolling its own
    JSON encoding just to fit one cache.
    """

    def __init__(self, client: Redis | None = None) -> None:
        self._client = client or get_redis_client()

    def get(self, key: str) -> object | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return pickle.loads(raw)

    def set(self, key: str, value: object, ttl_seconds: float) -> None:
        self._client.set(key, pickle.dumps(value), ex=max(1, round(ttl_seconds)))

    def delete(self, key: str) -> None:
        self._client.delete(key)
