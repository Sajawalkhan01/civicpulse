from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain.enums import Category, Priority, Status
from app.models import Complaint


class ComplaintNotFoundError(Exception):
    def __init__(self, complaint_id: UUID) -> None:
        self.complaint_id = complaint_id
        super().__init__(f"Complaint {complaint_id} not found")


@dataclass(frozen=True, slots=True)
class NewComplaint:
    text: str
    location: str
    category: Category
    priority: Priority
    triaged_by: str
    triage_latency_ms: int
    reporter_contact: str | None = None
    ai_summary: str | None = None
    status: Status = Status.OPEN


class ComplaintRepository:
    """All SQL/ORM query logic for the complaints table lives here."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: NewComplaint) -> Complaint:
        complaint = Complaint(
            text=data.text,
            location=data.location,
            reporter_contact=data.reporter_contact,
            category=data.category,
            priority=data.priority,
            status=data.status,
            ai_summary=data.ai_summary,
            triaged_by=data.triaged_by,
            triage_latency_ms=data.triage_latency_ms,
        )
        self._session.add(complaint)
        self._session.commit()
        self._session.refresh(complaint)
        return complaint

    def create_with_id(self, complaint_id: UUID, data: NewComplaint) -> bool:
        """Idempotent insert with a caller-supplied id.

        Used by the seed script so re-running it never duplicates rows.
        Returns True if a row was inserted, False if `complaint_id` already existed.
        """
        stmt = (
            pg_insert(Complaint)
            .values(
                id=complaint_id,
                text=data.text,
                location=data.location,
                reporter_contact=data.reporter_contact,
                category=data.category,
                priority=data.priority,
                status=data.status,
                ai_summary=data.ai_summary,
                triaged_by=data.triaged_by,
                triage_latency_ms=data.triage_latency_ms,
            )
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(Complaint.id)
        )
        result = self._session.execute(stmt)
        self._session.commit()
        return result.first() is not None

    def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        return self._session.get(Complaint, complaint_id)

    def list(
        self,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Complaint], int]:
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1:
            raise ValueError("page_size must be >= 1")

        filters = []
        if category is not None:
            filters.append(Complaint.category == category)
        if priority is not None:
            filters.append(Complaint.priority == priority)
        if status is not None:
            filters.append(Complaint.status == status)

        count_stmt = select(func.count()).select_from(Complaint)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = self._session.scalar(count_stmt) or 0

        list_stmt = select(Complaint)
        if filters:
            list_stmt = list_stmt.where(*filters)
        list_stmt = (
            list_stmt.order_by(Complaint.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(self._session.scalars(list_stmt).all())
        return rows, total

    def update_status(self, complaint_id: UUID, new_status: Status) -> Complaint:
        complaint = self._session.get(Complaint, complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)
        complaint.status = new_status
        complaint.updated_at = datetime.now(timezone.utc)
        self._session.commit()
        self._session.refresh(complaint)
        return complaint

    def stats(self) -> dict[str, dict[str, int]]:
        by_category = self._session.execute(
            select(Complaint.category, func.count()).group_by(Complaint.category)
        ).all()
        by_priority = self._session.execute(
            select(Complaint.priority, func.count()).group_by(Complaint.priority)
        ).all()
        return {
            "by_category": {category.value: count for category, count in by_category},
            "by_priority": {priority.value: count for priority, count in by_priority},
        }
