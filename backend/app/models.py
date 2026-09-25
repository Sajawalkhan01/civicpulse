import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.domain.enums import Category, Priority, Status


def _enum_values(enum_cls: type) -> list[str]:
    return [member.value for member in enum_cls]


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    text: Mapped[str] = mapped_column(sa.String(2000), nullable=False)
    location: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    category: Mapped[Category] = mapped_column(
        sa.Enum(Category, name="complaint_category", values_callable=_enum_values),
        nullable=False,
    )
    priority: Mapped[Priority] = mapped_column(
        sa.Enum(Priority, name="complaint_priority", values_callable=_enum_values),
        nullable=False,
    )
    status: Mapped[Status] = mapped_column(
        sa.Enum(Status, name="complaint_status", values_callable=_enum_values),
        nullable=False,
        default=Status.OPEN,
        server_default=sa.text("'open'"),
    )
    ai_summary: Mapped[str | None] = mapped_column(sa.String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
    )

    __table_args__ = (
        sa.CheckConstraint(
            "char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"
        ),
        sa.CheckConstraint(
            "char_length(location) BETWEEN 3 AND 200",
            name="ck_complaints_location_length",
        ),
        sa.Index("ix_complaints_status_priority", "status", "priority"),
        sa.Index("ix_complaints_created_at", "created_at"),
    )
