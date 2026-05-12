"""Environment variables loaded via pydantic-settings (`.env` in package root)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_env_paths() -> tuple[Path, ...]:
    """Resolve `.env` next to backend package root (`packages/backend/.env`)."""
    backend_root = Path(__file__).resolve().parents[2]
    return (backend_root / ".env",)


class AppEnv(BaseSettings):
    """Application / Django settings sourced from OS env and `.env`."""

    model_config = SettingsConfigDict(
        env_file=_default_env_paths(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
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

    django_allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "::1"]
    )

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3800"])

    @field_validator("django_allowed_hosts", "cors_origins", mode="before")
    @classmethod
    def _parse_csv_or_json_str(cls, value: Any) -> Any:
        if value is None or isinstance(value, list):
            return value
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            parsed: list[Any] = json.loads(text)
            return [str(x).strip() for x in parsed if str(x).strip()]
        return [p.strip() for p in text.split(",") if p.strip()]


@lru_cache
def get_env() -> AppEnv:
    """Cached env singleton (respects `@lru_cache` for reuse across Django settings imports)."""
    return AppEnv()
