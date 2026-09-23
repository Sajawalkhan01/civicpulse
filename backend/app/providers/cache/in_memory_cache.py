import time
from dataclasses import dataclass, field


@dataclass
class InMemoryCache:
    """TTL cache used when REDIS_URL isn't set (local dev without Redis).

    Process-local only -- doesn't survive a restart and isn't shared across
    multiple backend instances. See RedisCache for the horizontally-scalable
    version that's used whenever Redis is configured.
    """

    _store: dict[str, tuple[float, object]] = field(default_factory=dict)

    def get(self, key: str) -> object | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: object, ttl_seconds: float) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
