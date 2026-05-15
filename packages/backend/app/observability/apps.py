from django.apps import AppConfig


class ObservabilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.observability"
    label = "observability"

    def ready(self) -> None:
        import app.observability.signal_handlers  # noqa: F401
