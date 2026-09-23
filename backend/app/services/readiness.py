from sqlalchemy import text
from sqlalchemy.orm import Session

from app.providers.redis_client import get_redis_client


def is_database_ready(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def is_redis_ready() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False
