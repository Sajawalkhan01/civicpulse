from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.enums import Category, Priority, Status
from app.domain.models import ComplaintCreate, ComplaintListOut, ComplaintOut, StatusUpdate
from app.services import complaints as complaints_service

router = APIRouter(prefix="/api", tags=["complaints"])


@router.post("/complaints", status_code=201, response_model=ComplaintOut)
def create_complaint(data: ComplaintCreate, session: Session = Depends(get_session)) -> ComplaintOut:
    complaint = complaints_service.create_complaint(session, data)
    return ComplaintOut.model_validate(complaint)


@router.get("/complaints/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: UUID, session: Session = Depends(get_session)) -> ComplaintOut:
    complaint = complaints_service.get_complaint(session, complaint_id)
    return ComplaintOut.model_validate(complaint)


@router.get("/complaints", response_model=ComplaintListOut)
def list_complaints(
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> ComplaintListOut:
    items, total = complaints_service.list_complaints(
        session, category=category, priority=priority, status=status, page=page, page_size=page_size
    )
    return ComplaintListOut(items=[ComplaintOut.model_validate(item) for item in items], total=total)


@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintOut)
def update_complaint_status(
    complaint_id: UUID, body: StatusUpdate, session: Session = Depends(get_session)
) -> ComplaintOut:
    complaint = complaints_service.update_complaint_status(session, complaint_id, body.status)
    return ComplaintOut.model_validate(complaint)
