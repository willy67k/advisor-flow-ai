"""Pytest settings: Postgres (pgvector) by default — fast hashers — no reliance on risky secrets."""

import os

from app.config.database_url import django_postgres_settings
from app.config.settings.base import *  # noqa: F403

_test_db_url = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://advisorflow:advisorflow@127.0.0.1:5432/advisorflow",
)

DATABASES = {"default": django_postgres_settings(_test_db_url)}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SECRET_KEY = "test-secret-key-not-for-production"

# Celery: run tasks inline in CI/pytest — no Redis required.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

OBSERVABILITY_LOG_TO_DB = False
