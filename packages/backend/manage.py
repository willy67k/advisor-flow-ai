#!/usr/bin/env python
"""Django's command-line utility (default settings: ``app.config.settings.dev``)."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - startup guard
        raise ImportError("Could not import Django. Is it installed?") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
