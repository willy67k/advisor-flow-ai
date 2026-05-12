"""Parse ``DATABASE_URL`` for Django PostgreSQL configuration."""

from __future__ import annotations

from urllib.parse import unquote, urlparse


def django_postgres_settings(database_url: str) -> dict[str, object]:
    normalized = database_url.strip()
    for prefix in ("postgresql+psycopg://", "postgresql+psycopg2://"):
        normalized = normalized.replace(prefix, "postgresql://", 1)
    parsed = urlparse(normalized)
    db_name = (parsed.path or "/").lstrip("/")
    if not db_name:
        msg = "DATABASE_URL must include a database path (e.g. .../advisorflow)"
        raise ValueError(msg)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(db_name),
        "USER": unquote(parsed.username) if parsed.username else "",
        "PASSWORD": unquote(parsed.password) if parsed.password else "",
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
    }
