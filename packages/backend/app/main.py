"""ASGI entry for uvicorn: ``uvicorn app.main:app --reload``."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings.dev")

app = get_asgi_application()
