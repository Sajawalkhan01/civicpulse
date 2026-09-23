from typing import Protocol

from .models import TriageResult


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult: ...


class Cache(Protocol):
    """Shared by the triage content-hash cache and the /api/stats read-through
    cache. Implemented by InMemoryCache (local dev) and RedisCache (default
    whenever REDIS_URL is set) -- see providers/cache/factory.py."""

    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object, ttl_seconds: float) -> None: ...
    def delete(self, key: str) -> None: ...
