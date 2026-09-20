import os

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta/providers")
def get_providers() -> dict:
    return {
        "active_provider": os.environ.get("TRIAGE_PROVIDER", "unset"),
        # TODO(ai-layer chunk): populate with the real last-20-triage-outcomes
        # ring buffer.
        "recent_outcomes": [],
    }
