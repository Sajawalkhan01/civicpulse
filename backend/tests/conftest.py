import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.db import get_database_url


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
