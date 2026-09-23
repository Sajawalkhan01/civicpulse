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
