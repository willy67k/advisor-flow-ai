"""Environment variables loaded via pydantic-settings (`.env` in package root)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_env_paths() -> tuple[Path, ...]:
    """Resolve `.env` next to backend package root (`packages/backend/.env`)."""
    backend_root = Path(__file__).resolve().parents[2]
    return (backend_root / ".env",)


def _comma_or_json_list(raw: str | None, fallback: list[str]) -> list[str]:
    """Parse comma-separated or JSON-array env strings without pydantic JSON coercion."""
    if raw is None:
        return list(fallback)
    text = str(raw).strip()
    if not text:
        return list(fallback)
    if text.startswith("["):
        parsed: list[Any] = json.loads(text)
        return [str(x).strip() for x in parsed if str(x).strip()]
    return [p.strip() for p in text.split(",") if p.strip()]


class AppEnv(BaseSettings):
    """Application / Django settings sourced from OS env and `.env`."""

    model_config = SettingsConfigDict(
        env_file=_default_env_paths(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_ignore_empty=True,
    )

    app_name: str = "Advisor Flow AI"
    app_version: str = "0.0.1"
    environment: str = "development"
    log_level: str = "INFO"

    django_secret_key: str = Field(
        default="dev-insecure-secret-change-me-in-production-min-50-chars-aaaaaaaaaa",
        description="DJANGO_SECRET_KEY",
    )
    django_debug: bool = True

    django_allowed_hosts: str | None = Field(default=None)
    cors_origins: str | None = Field(default=None)

    database_url: str | None = Field(
        default=None,
        description="PostgreSQL/SQLAlchemy URL, e.g. postgresql://user:pass@localhost:5432/db",
    )

    celery_broker_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CELERY_BROKER_URL"),
        description="Redis URL for Celery broker, default redis://127.0.0.1:6379/0",
    )

    celery_task_always_eager: bool = Field(
        default=True,
        validation_alias=AliasChoices("CELERY_TASK_ALWAYS_EAGER"),
        description=(
            "When true (local dev default), Celery executes tasks in the caller process "
            "(no separate worker)."
        ),
    )

    langgraph_checkpoint_sqlite_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANGGRAPH_CHECKPOINT_SQLITE_PATH",
            "LANGGRAPH_CHECKPOINT_SQLITE",
        ),
        description=(
            "SQLite file path for LangGraph checkpoints (human-in-the-loop). "
            "Default: <backend>/langgraph_checkpoints.sqlite3"
        ),
    )

    openai_api_key: str | None = Field(default=None, description="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, description="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        description="GOOGLE_API_KEY or GEMINI_API_KEY (Gemini / Google GenAI)",
    )
    ai_openai_default_model: str = Field(
        default="gpt-4o-mini", description="AI_OPENAI_DEFAULT_MODEL"
    )
    ai_anthropic_default_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="AI_ANTHROPIC_DEFAULT_MODEL",
    )
    ai_gemini_default_model: str = Field(
        default="gemini-2.0-flash",
        description="AI_GEMINI_DEFAULT_MODEL",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("OPENAI_EMBEDDING_MODEL"),
        description="OpenAI embeddings model (Step 5.2 RAG chunks)",
    )

    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
        description="LangSmith / LangChain tracing API key (Step 8.1)",
    )
    langsmith_tracing_v2: bool = Field(
        default=True,
        validation_alias=AliasChoices("LANGCHAIN_TRACING_V2"),
        description="When false, tracing stays off even if an API key is set.",
    )
    langsmith_project: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGCHAIN_PROJECT", "LANGSMITH_PROJECT"),
        description="LangSmith project name (LANGCHAIN_PROJECT)",
    )
    langsmith_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGCHAIN_ENDPOINT", "LANGSMITH_ENDPOINT"),
        description="LangSmith API base URL (US default; EU uses https://eu.api.smith.langchain.com)",
    )
    observability_log_to_db: bool = Field(
        default=True,
        validation_alias=AliasChoices("OBSERVABILITY_LOG_TO_DB"),
        description="Persist Phase 8.2 structured events to ObservabilityLog (stderr always)",
    )

    def allowed_hosts_list(self) -> list[str]:
        return _comma_or_json_list(
            self.django_allowed_hosts,
            ["localhost", "127.0.0.1", "::1"],
        )

    def cors_origins_list(self) -> list[str]:
        return _comma_or_json_list(self.cors_origins, ["http://localhost:3800"])


@lru_cache
def get_env() -> AppEnv:
    """Cached env singleton (respects `@lru_cache` for reuse across Django settings imports)."""
    return AppEnv()
