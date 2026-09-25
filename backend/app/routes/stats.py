from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import complaints as complaints_service

router = APIRouter(prefix="/api", tags=["stats"])


@router.api_route("/stats", methods=["GET", "HEAD"])
def get_stats(response: Response, session: Session = Depends(get_session)) -> dict:
    stats, cache_hit = complaints_service.get_stats_cached(session)
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return stats
