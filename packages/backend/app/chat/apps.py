"""Django app: scoped AI workspace chat relay (streaming)."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.chat"
    label = "chat"
    verbose_name = "Workspace chat"
