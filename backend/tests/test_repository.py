"""Repository tests against a real Postgres instance (DATABASE_URL).

These exercise actual SQL (CHECK constraints, native enum types, server-side
defaults) that an in-memory SQLite substitute would not catch, so no mocking
or sqlite fallback is used here.
"""

import uuid

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db import get_database_url
from app.domain.enums import Category, Priority, Status
from app.models import Complaint
from app.repositories.complaints import (
    ComplaintNotFoundError,
    ComplaintRepository,
    NewComplaint,
)
from scripts.seed import seed as run_seed


@pytest.fixture(scope="session")
def engine():
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
def session(engine):
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = session_factory()
    created_ids: list[uuid.UUID] = []
    yield db_session, created_ids
    for complaint_id in created_ids:
        obj = db_session.get(Complaint, complaint_id)
        if obj is not None:
            db_session.delete(obj)
    db_session.commit()
    db_session.close()


@pytest.fixture
def repo(session):
    db_session, _ = session
    return ComplaintRepository(db_session)


def _new(**overrides) -> NewComplaint:
    kwargs = dict(
        text="Default test complaint text describing a civic issue in enough detail",
        location="Test Location, Test City",
        category=Category.WATER,
        priority=Priority.NORMAL,
        triaged_by="rules",
        triage_latency_ms=10,
    )
    kwargs.update(overrides)
    return NewComplaint(**kwargs)


def test_create_and_get_by_id_round_trip(repo, session):
    _, created_ids = session
    complaint = repo.create(
        _new(text="Round trip test complaint about a water leak issue near the market")
    )
    created_ids.append(complaint.id)

    fetched = repo.get_by_id(complaint.id)

    assert fetched is not None
    assert fetched.id == complaint.id
    assert fetched.text == complaint.text
    assert fetched.location == complaint.location
    assert fetched.category == Category.WATER
    assert fetched.status == Status.OPEN
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


def test_get_by_id_returns_none_for_missing_id(repo):
    assert repo.get_by_id(uuid.uuid4()) is None


def test_list_filters_by_category_and_priority(repo, session):
    _, created_ids = session
    marker = str(uuid.uuid4())[:8]
    matching = repo.create(
        _new(
            text=f"Filter test {marker} complaint about electricity transformer sparking",
            category=Category.ELECTRICITY,
            priority=Priority.HIGH,
        )
    )
    other_category = repo.create(
        _new(
            text=f"Filter test {marker} complaint about sanitation garbage collection",
            category=Category.SANITATION,
            priority=Priority.HIGH,
        )
    )
    other_priority = repo.create(
        _new(
            text=f"Filter test {marker} complaint about electricity meter billing issue",
            category=Category.ELECTRICITY,
            priority=Priority.LOW,
        )
    )
    created_ids.extend([matching.id, other_category.id, other_priority.id])

    results, total = repo.list(category=Category.ELECTRICITY, priority=Priority.HIGH)
    ids = {c.id for c in results}

    assert matching.id in ids
    assert other_category.id not in ids
    assert other_priority.id not in ids
    assert total >= 1


def test_list_paginates_a_known_slice(repo, session):
    _, created_ids = session
    category = Category.ROADS
    priority = Priority.LOW
    marker = str(uuid.uuid4())[:8]

    inserted = [
        repo.create(
            _new(
                text=f"Pagination test {marker} complaint number {i} about a minor road issue",
                location=f"Pagination Test Road {i}",
                category=category,
                priority=priority,
            )
        )
        for i in range(5)
    ]
    created_ids.extend(c.id for c in inserted)

    page1, total1 = repo.list(category=category, priority=priority, page=1, page_size=2)
    page2, total2 = repo.list(category=category, priority=priority, page=2, page_size=2)

    assert total1 == total2
    assert total1 >= 5
    assert len(page1) == 2
    assert len(page2) == 2
    assert {c.id for c in page1}.isdisjoint({c.id for c in page2})


def test_update_status_via_repository(repo, session):
    _, created_ids = session
    complaint = repo.create(
        _new(text="Status update test complaint about a broken streetlight near the park")
    )
    created_ids.append(complaint.id)
    assert complaint.status == Status.OPEN

    updated = repo.update_status(complaint.id, Status.IN_PROGRESS)

    assert updated.id == complaint.id
    assert updated.status == Status.IN_PROGRESS
    assert updated.updated_at >= complaint.updated_at

    refetched = repo.get_by_id(complaint.id)
    assert refetched.status == Status.IN_PROGRESS


def test_update_status_raises_for_missing_complaint(repo):
    with pytest.raises(ComplaintNotFoundError):
        repo.update_status(uuid.uuid4(), Status.IN_PROGRESS)


def test_seed_script_is_idempotent(engine):
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    first_session = session_factory()
    try:
        inserted_first, skipped_first = run_seed(first_session)
    finally:
        first_session.close()

    second_session = session_factory()
    try:
        inserted_second, skipped_second = run_seed(second_session)
    finally:
        second_session.close()

    assert inserted_first + skipped_first >= 30
    assert inserted_second == 0
    assert skipped_second == inserted_first + skipped_first
