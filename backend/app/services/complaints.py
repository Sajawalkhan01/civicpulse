from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.domain.enums import Category, Priority, Status
from app.domain.models import ComplaintCreate
from app.domain.state_machine import validate_transition
from app.models import Complaint
from app.providers.cache.factory import get_cache
from app.repositories.complaints import (
    ComplaintNotFoundError,
    ComplaintRepository,
    NewComplaint,
)
from app.services.triage_service import triage_service

_STATS_CACHE_KEY = "stats:summary:v1"
_STATS_CACHE_TTL_SECONDS = 30

_stats_cache = get_cache()


def create_complaint(session: Session, data: ComplaintCreate) -> Complaint:
    # Generated up front (rather than after insert) so the triage service has
    # a complaint id to put in its failure-fallback warning log.
    complaint_id = uuid4()
    result, triaged_by, latency_ms = triage_service.triage(
        complaint_id, data.text, data.location
    )

    new_complaint = NewComplaint(
        text=data.text,
        location=data.location,
        reporter_contact=data.reporter_contact,
        category=result.category,
        priority=result.priority,
        ai_summary=result.summary,
        triaged_by=triaged_by,
        triage_latency_ms=latency_ms,
    )
    repo = ComplaintRepository(session)
    repo.create_with_id(complaint_id, new_complaint)
    complaint = repo.get_by_id(complaint_id)
    assert complaint is not None
    invalidate_stats_cache()
    return complaint


def get_complaint(session: Session, complaint_id: UUID) -> Complaint:
    complaint = ComplaintRepository(session).get_by_id(complaint_id)
    if complaint is None:
        raise ComplaintNotFoundError(complaint_id)
    return complaint


def list_complaints(
    session: Session,
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Complaint], int]:
    return ComplaintRepository(session).list(
        category=category,
        priority=priority,
        status=status,
        page=page,
        page_size=page_size,
    )


def update_complaint_status(
    session: Session, complaint_id: UUID, new_status: Status
) -> Complaint:
    """The one function allowed to move a complaint's status (CLAUDE.md state machine rule)."""
    repo = ComplaintRepository(session)
    complaint = repo.get_by_id(complaint_id)
    if complaint is None:
        raise ComplaintNotFoundError(complaint_id)
    validate_transition(complaint.status, new_status)
    updated = repo.update_status(complaint_id, new_status)
    invalidate_stats_cache()
    return updated


def get_stats(session: Session) -> dict[str, dict[str, int]]:
    return ComplaintRepository(session).stats()


def get_stats_cached(session: Session) -> tuple[dict[str, dict[str, int]], bool]:
    """Read-through cache for GET /api/stats. Returns (stats, was_cache_hit)."""
    cached = _stats_cache.get(_STATS_CACHE_KEY)
    if cached is not None:
        return cached, True
    stats = get_stats(session)
    _stats_cache.set(_STATS_CACHE_KEY, stats, ttl_seconds=_STATS_CACHE_TTL_SECONDS)
    return stats, False


def invalidate_stats_cache() -> None:
    # Called on every complaint create/status change so a change is reflected
    # immediately instead of waiting out the rest of the 30s TTL.
    _stats_cache.delete(_STATS_CACHE_KEY)
