"""Alembic environment: resolves ``DATABASE_URL`` via pydantic settings (``.env``)."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config.env import get_env
from app.core.db import normalize_sqlalchemy_url
from app.models.meta import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _effective_url() -> str:
    url = get_env().database_url
    if not url:
        msg = "DATABASE_URL is not set — export it or add it to packages/backend/.env for Alembic."
        raise RuntimeError(msg)
    return normalize_sqlalchemy_url(url.strip())


def run_migrations_offline() -> None:
    url = _effective_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_effective_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
