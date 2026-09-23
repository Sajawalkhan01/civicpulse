from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.readiness import is_database_ready, is_redis_ready

router = APIRouter(tags=["health"])


@router.get("/ready")
def ready(response: Response, session: Session = Depends(get_session)) -> dict:
    if not is_database_ready(session):
        response.status_code = 503
        return {"status": "unavailable", "failed_dependency": "database"}
    if not is_redis_ready():
        response.status_code = 503
        return {"status": "unavailable", "failed_dependency": "redis"}
    return {"status": "ok"}
