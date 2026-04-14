"""
Database connection layer.

Provides a SQLAlchemy engine and session factory wired to DATABASE_URL from
settings.  Both are None when DATABASE_URL is not configured so callers can
skip DB work gracefully instead of crashing.

Usage:
    from app.database import get_session

    with get_session() as session:
        rows = session.execute(text("SELECT 1")).fetchall()

Or check availability first:
    from app.database import db_available
    if db_available():
        ...
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine = None
_SessionFactory = None

if settings.database_url:
    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,   # detect stale connections
        pool_size=5,
        max_overflow=10,
    )
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)


def db_available() -> bool:
    """Return True if a database URL was configured and a connection can be made."""
    if _engine is None:
        return False
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy Session, rolling back on error and always closing.

    Raises RuntimeError if no DATABASE_URL is configured.
    """
    if _SessionFactory is None:
        raise RuntimeError(
            "Database is not configured. Set DATABASE_URL in your environment or .env file."
        )
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
