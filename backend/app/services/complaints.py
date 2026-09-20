import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.enums import Category, Priority, Status
from app.domain.models import ComplaintCreate
from app.domain.protocols import TriageProvider
from app.domain.state_machine import validate_transition
from app.models import Complaint
from app.repositories.complaints import ComplaintNotFoundError, ComplaintRepository, NewComplaint
from app.services.triage_stub import StubTriageProvider

# TODO(next chunk): swap this for the real TriageProvider (providers/triage/).
_triage_provider: TriageProvider = StubTriageProvider()


def create_complaint(session: Session, data: ComplaintCreate) -> Complaint:
    started = time.perf_counter()
    triage = _triage_provider.triage(data.text, data.location)
    latency_ms = int((time.perf_counter() - started) * 1000)

    new_complaint = NewComplaint(
        text=data.text,
        location=data.location,
        reporter_contact=data.reporter_contact,
        category=triage.category,
        priority=triage.priority,
        ai_summary=triage.summary,
        triaged_by=_triage_provider.name,
        triage_latency_ms=latency_ms,
    )
    return ComplaintRepository(session).create(new_complaint)


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
        category=category, priority=priority, status=status, page=page, page_size=page_size
    )


def update_complaint_status(session: Session, complaint_id: UUID, new_status: Status) -> Complaint:
    """The one function allowed to move a complaint's status (CLAUDE.md state machine rule)."""
    repo = ComplaintRepository(session)
    complaint = repo.get_by_id(complaint_id)
    if complaint is None:
        raise ComplaintNotFoundError(complaint_id)
    validate_transition(complaint.status, new_status)
    return repo.update_status(complaint_id, new_status)


def get_stats(session: Session) -> dict[str, dict[str, int]]:
    return ComplaintRepository(session).stats()
