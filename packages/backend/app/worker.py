"""Celery application — run worker: ``celery -A app.worker:celery_app worker -l INFO``."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings.dev")

import django  # noqa: E402

django.setup()

from celery import Celery  # noqa: E402 - after Django configures settings/apps

celery_app = Celery("advisorflow")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

import app.meetings.tasks  # noqa: E402, F401 - register tasks after Django loads
