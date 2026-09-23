"""Cache layer tests against a real Redis (REDIS_URL from .env / the test
environment) -- covers the /api/stats read-through cache: MISS then HIT
within the 30s TTL, and MISS again immediately after invalidation (complaint
create or status change), rather than waiting out the TTL.
"""

import pytest

import app.services.complaints as complaints_service


def _complaint_payload(**overrides) -> dict:
    payload = {
        "text": "Cache test complaint describing a pothole in enough detail to pass validation",
        "location": "Cache Test Location, Test City",
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def _reset_stats_cache():
    """Every test in this file starts and ends with a cold stats cache, so
    tests never see a HIT left behind by a previous test."""
    complaints_service.invalidate_stats_cache()
    yield
    complaints_service.invalidate_stats_cache()


def test_stats_is_miss_then_hit_within_ttl(client):
    first = client.get("/api/stats")
    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"

    second = client.get("/api/stats")
    assert second.status_code == 200
    assert second.headers["x-cache"] == "HIT"
    assert second.json() == first.json()


def test_stats_cache_is_invalidated_on_complaint_create(client, created_ids):
    warm = client.get("/api/stats")
    assert warm.headers["x-cache"] == "MISS"
    still_cached = client.get("/api/stats")
    assert still_cached.headers["x-cache"] == "HIT"

    created = client.post("/api/complaints", json=_complaint_payload())
    assert created.status_code == 201
    created_ids.append(created.json()["id"])

    after_create = client.get("/api/stats")
    assert after_create.headers["x-cache"] == "MISS"


def test_stats_cache_is_invalidated_on_status_change(client, created_ids):
    created = client.post("/api/complaints", json=_complaint_payload())
    assert created.status_code == 201
    complaint_id = created.json()["id"]
    created_ids.append(complaint_id)

    warm = client.get("/api/stats")
    assert warm.status_code == 200
    still_cached = client.get("/api/stats")
    assert still_cached.headers["x-cache"] == "HIT"

    status_response = client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "in_progress"})
    assert status_response.status_code == 200

    after_update = client.get("/api/stats")
    assert after_update.headers["x-cache"] == "MISS"
