import os
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Loads backend/.env if present (never overrides real env vars already set,
# e.g. in prod/CI). A no-op if the file doesn't exist.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Point it at a reachable Postgres instance, e.g. "
            "postgresql://user:pass@localhost:5432/civicpulse"
        )
    # Only the psycopg (v3) driver is installed, but the plain "postgresql://"
    # scheme makes SQLAlchemy default to psycopg2. Normalize so either form works.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Base(DeclarativeBase):
    pass


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed after."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
