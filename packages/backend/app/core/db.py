"""SQLAlchemy engine factory (PostgreSQL via psycopg v3 dialect)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.env import get_env


def normalize_sqlalchemy_url(database_url: str) -> str:
    url = database_url.strip()
    if url.startswith("postgresql://"):
        remainder = url.removeprefix("postgresql://")
        if not remainder.startswith("+"):
            return f"postgresql+psycopg://{remainder}"
    return url


def get_sqlalchemy_engine() -> Engine | None:
    """Return SQLAlchemy engine when ``DATABASE_URL`` is set."""
    cfg = get_env()
    if not cfg.database_url:
        return None
    url = normalize_sqlalchemy_url(cfg.database_url)
    return create_engine(url, pool_pre_ping=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional ORM scope; rolls back on error."""
    engine = get_sqlalchemy_engine()
    if engine is None:
        msg = (
            "DATABASE_URL is required to open a SQLAlchemy session. "
            "Set it when using Alembic or SQLAlchemy features."
        )
        raise RuntimeError(msg)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
