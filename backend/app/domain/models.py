from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import Category, Priority, Status


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str | None
    triage_latency_ms: int | None
    created_at: datetime
    updated_at: datetime


class ComplaintListOut(BaseModel):
    items: list[ComplaintOut]
    total: int


class StatusUpdate(BaseModel):
    status: Status
