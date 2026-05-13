"""Development settings; default for `manage.py`, `uvicorn app.main:app`, and backend `yarn dev`."""

from app.config.env import get_env
from app.config.settings.base import *  # noqa: F403

_env = get_env()

CELERY_TASK_ALWAYS_EAGER = _env.celery_task_always_eager
CELERY_TASK_EAGER_PROPAGATES = True
