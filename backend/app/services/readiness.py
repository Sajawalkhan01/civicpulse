from sqlalchemy import text
from sqlalchemy.orm import Session


def is_database_ready(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
