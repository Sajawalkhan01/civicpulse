# Deliberately the ONLY import here is fastapi: /health must never touch the
# database, Redis, or any provider. It only confirms the process is up.
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
