"""SQLAlchemy Declarative base for Alembic autogenerate (tables land in Phase 2.3+)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Meta registry for Alembic ``target_metadata``."""
