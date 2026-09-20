from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.readiness import is_database_ready

router = APIRouter(tags=["health"])


@router.get("/ready")
def ready(response: Response, session: Session = Depends(get_session)) -> dict:
    # TODO(redis chunk): also check Redis connectivity here once it's wired in.
    if not is_database_ready(session):
        response.status_code = 503
        return {"status": "unavailable", "failed_dependency": "database"}
    return {"status": "ok"}
