import os

from redis import Redis

from app.providers.redis_client import get_redis_client

DEFAULT_LIMIT_PER_MINUTE = 60
_WINDOW_SECONDS = 60


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limit exceeded, retry after {retry_after_seconds}s")


class RedisRateLimiter:
    """Distributed fixed-window request counter, keyed by an arbitrary
    client key (the caller's IP). Backed by Redis rather than an in-process
    dict so the limit holds across however many backend instances are
    running behind the load balancer, not just one process's memory.

    Implementation choice -- pipelined INCR + EXPIRE(NX) under a MULTI/EXEC
    transaction, not a Lua/EVAL script:

    - INCR alone can't attach a TTL, and issuing EXPIRE as a second, separate
      round trip afterwards would race: two concurrent first-requests-in-a-
      window could both see the key freshly created and both (redundantly)
      call EXPIRE, or a crash between the two calls could leave the key
      permanently without a TTL. Sending both commands in one MULTI/EXEC
      pipeline closes that gap -- Redis executes a transaction's commands
      back to back with no other client's command interleaved, so from every
      other client's point of view INCR-then-EXPIRE happens as one step.
    - EXPIRE ... NX (Redis 7+) only attaches a TTL if the key doesn't already
      have one. That makes it fire exactly once per window, the moment INCR
      creates the key, and be a no-op on every later request in that same
      window. Without NX, every request would re-arm the TTL and the window
      would keep sliding forward on continuous traffic instead of resetting
      on a fixed cadence -- a client could then never fall back under the
      limit as long as it keeps requesting.
    - A Lua script via EVAL gives the same atomicity and is the more common
      way to see this pattern, but it means shipping a script body to Redis
      and reasoning about SCRIPT LOAD/EVALSHA/NOSCRIPT. Two pipelined
      built-in commands get the same fixed-window guarantee with less
      moving parts, so that's what's used here.
    """

    def __init__(
        self,
        client: Redis | None = None,
        limit: int | None = None,
        window_seconds: int = _WINDOW_SECONDS,
    ) -> None:
        self._client = client or get_redis_client()
        self._limit = (
            limit
            if limit is not None
            else int(os.environ.get("RATE_LIMIT_PER_MINUTE", DEFAULT_LIMIT_PER_MINUTE))
        )
        self._window_seconds = window_seconds

    def check(self, client_key: str) -> None:
        """Raises RateLimitExceeded if client_key is over the limit for the current window."""
        redis_key = f"ratelimit:{client_key}"
        pipe = self._client.pipeline(transaction=True)
        pipe.incr(redis_key)
        pipe.expire(redis_key, self._window_seconds, nx=True)
        count, _ = pipe.execute()

        if count > self._limit:
            ttl = self._client.ttl(redis_key)
            retry_after = ttl if ttl and ttl > 0 else self._window_seconds
            raise RateLimitExceeded(retry_after_seconds=retry_after)


_limiter: RedisRateLimiter | None = None


def get_rate_limiter() -> RedisRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RedisRateLimiter()
    return _limiter
