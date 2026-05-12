from app.config.database_url import django_postgres_settings
from app.core.db import normalize_sqlalchemy_url


def test_django_postgres_from_standard_url():
    cfg = django_postgres_settings("postgresql://u:secret@db.internal:5544/mydb")
    assert cfg["ENGINE"] == "django.db.backends.postgresql"
    assert cfg["NAME"] == "mydb"
    assert cfg["USER"] == "u"
    assert cfg["PASSWORD"] == "secret"
    assert cfg["HOST"] == "db.internal"
    assert cfg["PORT"] == "5544"


def test_django_postgres_strips_psycopg_scheme():
    cfg = django_postgres_settings(
        "postgresql+psycopg://alpha:beta%40@localhost/advisorflow",
    )
    assert cfg["PASSWORD"] == "beta@"
    assert cfg["USER"] == "alpha"


def test_sqlalchemy_normalize_adds_psycopg_driver():
    out = normalize_sqlalchemy_url("postgresql://x:y@localhost:5432/db")
    assert out == "postgresql+psycopg://x:y@localhost:5432/db"
