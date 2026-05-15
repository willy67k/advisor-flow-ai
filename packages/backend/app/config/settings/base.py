"""Shared Django settings. Values merged from pydantic-loaded environment (`app.config.env`)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from app.config.database_url import django_postgres_settings
from app.config.env import get_env
from app.observability.langsmith_bootstrap import configure_langsmith_envvars
from app.observability.tracer import configure_structlog

_env = get_env()
configure_langsmith_envvars()
configure_structlog()

# Build paths: packages/backend/
BASE_DIR = Path(__file__).resolve().parents[3]

SECRET_KEY = _env.django_secret_key
DEBUG = _env.django_debug
ALLOWED_HOSTS = list(_env.allowed_hosts_list())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.observability.apps.ObservabilityConfig",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_celery_results",
    "app.accounts",
    "app.clients",
    "app.meetings",
    "app.documents",
    "app.workflows",
    "app.approvals.apps.ApprovalsConfig",
    "app.compliance.apps.ComplianceConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "app.middleware.audit_actor.AuditActorMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# PostgreSQL via ``DATABASE_URL`` when set; otherwise SQLite file (offline / tests without Docker).
if _env.database_url:
    DATABASES = {"default": django_postgres_settings(_env.database_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

AUTH_USER_MODEL = "accounts.User"

# CORS — explicit origins from env (`CORS_ORIGINS`)
CORS_ALLOWED_ORIGINS = list(_env.cors_origins_list())
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AdvisorFlow AI API",
    "DESCRIPTION": "Backend REST API for AdvisorFlow AI.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Redis broker + django-celery-results persistence
CELERY_BROKER_URL = _env.celery_broker_url or "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_TASK_TRACK_STARTED = True

# LangGraph durable checkpoints (interrupt / resume) — shared path for web + Celery worker on one host/volume
LANGGRAPH_CHECKPOINT_SQLITE_PATH = (
    Path(_env.langgraph_checkpoint_sqlite_path)
    if _env.langgraph_checkpoint_sqlite_path
    else BASE_DIR / "langgraph_checkpoints.sqlite3"
)

# Duplicate structlog-style events to Postgres (disable in tests via settings.test).
OBSERVABILITY_LOG_TO_DB = _env.observability_log_to_db
