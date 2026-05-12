from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "accounts"
    name = "app.accounts"
    verbose_name = "Accounts"
