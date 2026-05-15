from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.workflows"
    label = "workflows"

    def ready(self) -> None:
        import app.workflows.signals  # noqa: F401
