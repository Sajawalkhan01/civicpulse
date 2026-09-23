import os

# Tests must never depend on, or be silently overridden by, whatever happens
# to be in the ambient shell environment (e.g. a developer's TRIAGE_PROVIDER=
# llm / GROQ_API_KEY left set from manual testing). This has to run *before*
# app.main is imported below: app.services.triage_service builds its provider
# singleton exactly once, at import time, from these env vars — a monkeypatch
# fixture applied during a test would already be too late.
os.environ["TRIAGE_PROVIDER"] = "simulated"
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("OLLAMA_BASE_URL", None)
os.environ.pop("OLLAMA_MODEL", None)

import uuid
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.db import get_database_url
from app.main import app
from app.models import Complaint
from app.services.triage_service import triage_service as _triage_service


@pytest.fixture(scope="session")
def engine() -> Engine:
    eng = create_engine(get_database_url())
    # Schema comes only from `alembic upgrade head` (per CLAUDE.md, no
    # CREATE TABLE outside the migration) — fail with a clear message
    # instead of a raw Postgres error if it hasn't been applied yet.
    if not inspect(eng).has_table("complaints"):
        pytest.fail(
            "The 'complaints' table does not exist on DATABASE_URL. "
            "Run `alembic upgrade head` against the test database first."
        )
    yield eng
    eng.dispose()


@pytest.fixture
def created_ids() -> list[str]:
    """Complaint ids a test created via the API; cleaned up automatically."""
    return []


@pytest.fixture(autouse=True)
def _cleanup_created_complaints(engine, created_ids):
    yield
    if not created_ids:
        return
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        for raw_id in created_ids:
            obj = session.get(Complaint, uuid.UUID(str(raw_id)))
            if obj is not None:
                session.delete(obj)
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _enforce_simulated_triage_provider():
    """Belt-and-suspenders: fail loudly rather than hit a real API.

    The env vars are already forced to safe values at module import time
    above; this just guards against something re-creating the singleton
    (or a future refactor) reintroducing a live provider into the test run.
    """
    assert _triage_service.active_provider_name == "simulated", (
        "Tests must run against TRIAGE_PROVIDER=simulated, but the active "
        f"triage provider is {_triage_service.active_provider_name!r}. "
        "Refusing to run tests that could hit a real provider API."
    )
    yield
