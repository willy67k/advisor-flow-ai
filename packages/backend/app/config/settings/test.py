"""Pytest / CI settings: in-memory DB, fast hashers, no reliance on local `.env` secrets."""

from app.config.settings.base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SECRET_KEY = "test-secret-key-not-for-production"
