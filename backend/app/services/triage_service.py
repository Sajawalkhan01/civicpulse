import hashlib
import logging
import random
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Protocol

from app.domain.models import TriageResult
from app.domain.protocols import TriageProvider
from app.providers.triage.factory import get_triage_provider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.base import RetryableTriageError

logger = logging.getLogger("civicpulse.triage")

_CACHE_TTL_SECONDS = 24 * 60 * 60


class Cache(Protocol):
    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object, ttl_seconds: float) -> None: ...


@dataclass
class InMemoryCache:
    """TTL cache for triage outcomes. A Redis-backed Cache comes next chunk."""

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


@dataclass
class TriageOutcome:
    provider: str
    latency_ms: int
    fell_back: bool
    cache_hit: bool


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, RetryableTriageError)


class TriageService:
    """Orchestration logic, independent of which provider is active."""

    def __init__(
        self,
        provider: TriageProvider,
        cache: Cache | None = None,
        timeout_seconds: float = 10.0,
        retry_delay_range: tuple[float, float] = (0.1, 0.3),
        ring_buffer_size: int = 20,
    ) -> None:
        self._provider = provider
        self._fallback = RuleBasedTriage()
        self._cache = cache if cache is not None else InMemoryCache()
        self._timeout_seconds = timeout_seconds
        self._retry_delay_range = retry_delay_range
        self._outcomes: deque[TriageOutcome] = deque(maxlen=ring_buffer_size)
        self._cache_hits = 0
        self._cache_lookups = 0

    @property
    def active_provider_name(self) -> str:
        return self._provider.name

    @property
    def recent_outcomes(self) -> list[TriageOutcome]:
        return list(self._outcomes)

    @property
    def cache_hit_rate(self) -> float:
        if self._cache_lookups == 0:
            return 0.0
        return self._cache_hits / self._cache_lookups

    def triage(self, complaint_id: uuid.UUID, text: str, location: str) -> tuple[TriageResult, str, int]:
        """Returns (result, triaged_by, latency_ms)."""
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        self._cache_lookups += 1
        cached = self._cache.get(content_hash)
        if cached is not None:
            self._cache_hits += 1
            result, triaged_by = cached
            self._record_outcome(triaged_by, latency_ms=0, fell_back=triaged_by == "rules:fallback", cache_hit=True)
            return result, triaged_by, 0

        started = time.perf_counter()
        fell_back = False
        try:
            result = self._run_provider_with_retry(text, location)
            triaged_by = self._provider.name
        except Exception as exc:
            logger.warning(
                "triage provider failed, falling back to rules",
                extra={
                    "complaint_id": str(complaint_id),
                    "provider": self._provider.name,
                    "exception_class": type(exc).__name__,
                },
            )
            result = self._fallback.triage(text, location)
            triaged_by = "rules:fallback"
            fell_back = True

        latency_ms = int((time.perf_counter() - started) * 1000)
        self._cache.set(content_hash, (result, triaged_by), ttl_seconds=_CACHE_TTL_SECONDS)
        self._record_outcome(triaged_by, latency_ms, fell_back, cache_hit=False)
        return result, triaged_by, latency_ms

    def _run_provider_with_retry(self, text: str, location: str) -> TriageResult:
        last_exc: Exception | None = None
        for attempt in range(2):  # original attempt + at most one retry
            try:
                return self._call_with_hard_timeout(text, location)
            except Exception as exc:
                last_exc = exc
                if attempt == 0 and _is_retryable(exc):
                    time.sleep(random.uniform(*self._retry_delay_range))
                    continue
                break
        assert last_exc is not None
        raise last_exc

    def _call_with_hard_timeout(self, text: str, location: str) -> TriageResult:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._provider.triage, text, location)
            try:
                return future.result(timeout=self._timeout_seconds)
            except FutureTimeoutError as exc:
                raise RetryableTriageError(
                    f"Triage provider {self._provider.name!r} exceeded {self._timeout_seconds}s"
                ) from exc

    def _record_outcome(self, provider: str, latency_ms: int, fell_back: bool, cache_hit: bool) -> None:
        self._outcomes.append(
            TriageOutcome(provider=provider, latency_ms=latency_ms, fell_back=fell_back, cache_hit=cache_hit)
        )


# Shared singleton: services/complaints.py triages through it, routes/meta.py
# reads its ring buffer/cache stats. Provider chosen once at import time from
# TRIAGE_PROVIDER (see providers/triage/factory.py).
triage_service = TriageService(provider=get_triage_provider())
