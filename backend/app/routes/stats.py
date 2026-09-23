from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import complaints as complaints_service

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def get_stats(session: Session = Depends(get_session)) -> dict:
    # TODO(redis chunk): cache this response in Redis; computed live from
    # Postgres for now.
    return complaints_service.get_stats(session)
