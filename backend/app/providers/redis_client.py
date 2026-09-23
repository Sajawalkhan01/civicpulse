import os

from redis import Redis

_client: Redis | None = None


def get_redis_url() -> str | None:
    return os.environ.get("REDIS_URL")


def get_redis_client() -> Redis:
    """Process-wide Redis connection, shared by the cache, the rate limiter,
    and the /ready check. redis-py pools connections internally, so one
    client instance is safe to reuse across requests and threads."""
    global _client
    if _client is None:
        url = get_redis_url()
        if not url:
            raise RuntimeError(
                "REDIS_URL environment variable is not set. "
                "Point it at a reachable Redis instance, e.g. redis://localhost:6379/0"
            )
        _client = Redis.from_url(url)
    return _client
