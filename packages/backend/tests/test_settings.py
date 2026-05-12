"""Smoke tests ensuring Django configures with layered settings."""

import pytest


@pytest.mark.django_db
def test_settings_configured(settings):
    assert settings.configured
    assert settings.SECRET_KEY
    assert "django.contrib.admin" in settings.INSTALLED_APPS
    assert "corsheaders" in settings.INSTALLED_APPS
    assert "memory" in str(settings.DATABASES["default"]["NAME"]).lower()
