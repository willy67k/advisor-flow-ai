# Django + Uvicorn (`packages/backend`).
# Compose build `context:` is repo root (`.`) — paths below are relative to that context.
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=app.config.settings.dev

COPY packages/backend/pyproject.toml packages/backend/uv.lock packages/backend/README.md packages/backend/manage.py packages/backend/alembic.ini ./
COPY packages/backend/app ./app
COPY packages/backend/alembic ./alembic

RUN uv sync --frozen --no-dev \
    && uv pip install --no-cache-dir flower

RUN mkdir -p /app/langgraph_data /app/media

EXPOSE 3801

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3801"]
