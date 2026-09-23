from dataclasses import asdict

from fastapi import APIRouter

from app.services.triage_service import triage_service

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta/providers")
def get_providers() -> dict:
    return {
        "active_provider": triage_service.active_provider_name,
        "recent_outcomes": [asdict(outcome) for outcome in triage_service.recent_outcomes],
        "cache_hit_rate": triage_service.cache_hit_rate,
    }
