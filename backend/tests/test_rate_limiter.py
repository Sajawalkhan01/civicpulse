"""Rate limiter tests against a real Redis (REDIS_URL) and the real
POST /api/complaints route, going through RateLimitMiddleware end to end.

Uses a short test-only limit/window (3 requests / 10s) instead of the real
RATE_LIMIT_PER_MINUTE default so the "window passes" case doesn't need a real
minute-long sleep. Each test sends a distinct X-Forwarded-For IP so its
counter key doesn't collide with the "testclient" key every other test in
the suite implicitly uses (their real client_ip defaults to the TestClient's
fixed host), and with other tests in this file run in the same session.
"""

import time

import pytest

import app.middleware.rate_limit as rate_limit_middleware
from app.providers.rate_limiter import RedisRateLimiter
from app.providers.redis_client import get_redis_client

_TEST_LIMIT = 3
_TEST_WINDOW_SECONDS = 10


def _complaint_payload(**overrides) -> dict:
    payload = {
        "text": "Rate limiter test complaint describing a broken streetlight downtown",
        "location": "Rate Limit Test Location, Test City",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def small_limit(monkeypatch):
    """Swaps in a 3-requests/10s limiter for the duration of one test, and
    cleans up its Redis counter key afterwards."""
    limiter = RedisRateLimiter(limit=_TEST_LIMIT, window_seconds=_TEST_WINDOW_SECONDS)
    monkeypatch.setattr(rate_limit_middleware, "get_rate_limiter", lambda: limiter)
    yield limiter


def _flush_key(client_ip: str) -> None:
    get_redis_client().delete(f"ratelimit:{client_ip}")


def test_exceeding_limit_returns_429_with_retry_after(client, created_ids, small_limit):
    client_ip = "203.0.113.10"
    _flush_key(client_ip)
    headers = {"X-Forwarded-For": client_ip}

    try:
        for _ in range(_TEST_LIMIT):
            response = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
            assert response.status_code == 201, response.text
            created_ids.append(response.json()["id"])

        limited = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
        assert limited.status_code == 429
        retry_after = int(limited.headers["retry-after"])
        assert 0 < retry_after <= _TEST_WINDOW_SECONDS
    finally:
        _flush_key(client_ip)


def test_requests_allowed_again_after_window_passes(client, created_ids, small_limit):
    client_ip = "203.0.113.11"
    _flush_key(client_ip)
    headers = {"X-Forwarded-For": client_ip}

    try:
        for _ in range(_TEST_LIMIT):
            response = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
            assert response.status_code == 201, response.text
            created_ids.append(response.json()["id"])

        limited = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
        assert limited.status_code == 429

        time.sleep(_TEST_WINDOW_SECONDS + 1)

        recovered = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
        assert recovered.status_code == 201, recovered.text
        created_ids.append(recovered.json()["id"])
    finally:
        _flush_key(client_ip)


def test_only_the_last_forwarded_for_hop_is_trusted(client, created_ids, small_limit):
    """A spoofed front of the X-Forwarded-For chain must not let a client
    dodge the limit by claiming a different IP on every request -- only the
    last hop (the one nginx itself would append) is used as the rate-limit
    key."""
    real_ip = "203.0.113.12"
    _flush_key(real_ip)

    try:
        for i in range(_TEST_LIMIT):
            spoofed_front = f"1.2.3.{i}"
            headers = {"X-Forwarded-For": f"{spoofed_front}, {real_ip}"}
            response = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
            assert response.status_code == 201, response.text
            created_ids.append(response.json()["id"])

        headers = {"X-Forwarded-For": f"9.9.9.9, {real_ip}"}
        limited = client.post("/api/complaints", json=_complaint_payload(), headers=headers)
        assert limited.status_code == 429
    finally:
        _flush_key(real_ip)
