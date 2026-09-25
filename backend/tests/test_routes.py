"""Route tests against the real FastAPI app and a real Postgres instance.

Uses FastAPI's TestClient end to end (no mocking of the DB) so these exercise
the actual routes -> services -> repository stack against DATABASE_URL, the
same database as test_repository.py.
"""

import uuid

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app

# `engine`, `created_ids`, `_cleanup_created_complaints`, and `client` fixtures
# come from tests/conftest.py (shared with test_triage.py).


def _create_complaint(client: TestClient, created_ids: list[str], **overrides) -> dict:
    payload = {
        "text": "Default route test complaint describing a civic issue in detail",
        "location": "Route Test Location, Test City",
    }
    payload.update(overrides)
    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    created_ids.append(body["id"])
    return body


# --- POST /api/complaints ---------------------------------------------------


def test_create_complaint_happy_path(client, created_ids):
    body = _create_complaint(
        client,
        created_ids,
        text="Burst pipe near the market flooding the main road since morning",
        location="Test Market Road, Lahore",
        reporter_contact="0300-1111111",
    )
    assert body["category"] in {
        "water",
        "electricity",
        "sanitation",
        "roads",
        "streetlights",
        "other",
    }
    assert body["priority"] in {"high", "normal", "low"}
    assert body["status"] == "open"
    assert body["ai_summary"]
    assert (
        body["triaged_by"] == "simulated"
    )  # TRIAGE_PROVIDER=simulated, mode="normal" never fails
    assert body["triage_latency_ms"] >= 0
    assert body["reporter_contact"] == "0300-1111111"
    uuid.UUID(body["id"])  # raises if not a valid UUID


def test_create_complaint_returns_400_on_invalid_input(client):
    response = client.post(
        "/api/complaints", json={"text": "too short", "location": "X"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "validation_error"
    field_names = {f["field"] for f in body["fields"]}
    assert "text" in field_names
    assert "location" in field_names


# --- GET /api/complaints/{id} ------------------------------------------------


def test_get_complaint_happy_path(client, created_ids):
    created = _create_complaint(client, created_ids)
    response = client.get(f"/api/complaints/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_complaint_returns_404_for_missing_id(client):
    response = client.get(f"/api/complaints/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


# --- GET /api/complaints (list) ---------------------------------------------


def test_list_complaints_happy_path(client, created_ids):
    marker_location = f"List Route Test {uuid.uuid4()}"
    _create_complaint(client, created_ids, location=marker_location)
    _create_complaint(client, created_ids, location=marker_location)

    response = client.get(
        "/api/complaints",
        params={"category": "other", "priority": "normal", "page_size": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert "items" in body and "total" in body
    assert body["total"] >= 2
    assert len(body["items"]) == 1


def test_list_complaints_rejects_page_size_over_100(client):
    response = client.get("/api/complaints", params={"page_size": 101})
    assert response.status_code == 400


# --- PATCH /api/complaints/{id}/status --------------------------------------


def test_update_status_happy_path(client, created_ids):
    created = _create_complaint(client, created_ids)
    response = client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_status_returns_409_on_illegal_transition(client, created_ids):
    created = _create_complaint(client, created_ids)
    complaint_id = created["id"]

    first = client.patch(
        f"/api/complaints/{complaint_id}/status", json={"status": "in_progress"}
    )
    assert first.status_code == 200
    second = client.patch(
        f"/api/complaints/{complaint_id}/status", json={"status": "resolved"}
    )
    assert second.status_code == 200

    third = client.patch(
        f"/api/complaints/{complaint_id}/status", json={"status": "in_progress"}
    )
    assert third.status_code == 409
    assert third.json() == {
        "error": "invalid_transition",
        "from": "resolved",
        "to": "in_progress",
        "message": "Cannot transition from resolved to in_progress",
    }


def test_update_status_returns_404_for_missing_complaint(client):
    response = client.patch(
        f"/api/complaints/{uuid.uuid4()}/status", json={"status": "in_progress"}
    )
    assert response.status_code == 404


# --- GET /api/stats -----------------------------------------------------


def test_stats_happy_path(client, created_ids):
    _create_complaint(client, created_ids)
    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert "by_category" in body
    assert "by_priority" in body


# --- GET /api/meta/providers -------------------------------------------


def test_meta_providers_happy_path(client):
    response = client.get("/api/meta/providers")
    assert response.status_code == 200
    body = response.json()
    assert "active_provider" in body
    # recent_outcomes/cache_hit_rate reflect real, cross-test shared state
    # (the ring buffer), so just check the shape rather than exact contents.
    assert isinstance(body["recent_outcomes"], list)
    assert isinstance(body["cache_hit_rate"], float)


# --- GET /health / /ready / /metrics ------------------------------------


def test_health_happy_path(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ok_even_with_broken_database_url(monkeypatch, client):
    """/health must not care about the database (CLAUDE.md hard requirement).

    Breaks DATABASE_URL AND forces the DB session dependency to raise if
    anything ever calls it, so this fails loudly if /health is ever changed
    to touch the database — not just when the env var happens to matter.
    """

    def _broken_session():
        raise RuntimeError("database is intentionally broken for this test")
        yield  # pragma: no cover - never reached, makes this a generator

    monkeypatch.setenv("DATABASE_URL", "postgresql://bad:bad@localhost:1/doesnotexist")
    app.dependency_overrides[get_session] = _broken_session
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_happy_path(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_happy_path(client):
    client.get("/health")  # generate at least one request to count
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "triage_latency_seconds" in response.text
    assert "triage_fallback_total" in response.text


# --- request id propagation (explicit requirement) -----------------------


def test_response_echoes_incoming_request_id_header(client):
    response = client.get("/health", headers={"X-Request-ID": "test-fixed-id"})
    assert response.headers["x-request-id"] == "test-fixed-id"


def test_response_generates_request_id_when_absent(client):
    response = client.get("/health")
    assert uuid.UUID(response.headers["x-request-id"])
