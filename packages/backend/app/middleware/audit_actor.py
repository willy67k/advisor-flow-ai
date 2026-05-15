"""Bind authenticated user to request thread for audit logging — Step 7.2."""

from __future__ import annotations

import threading
from typing import Any

_ctx = threading.local()


def get_audit_actor():
    """Return the user bound by ``AuditActorMiddleware`` for the current thread, if any."""
    return getattr(_ctx, "user", None)


class AuditActorMiddleware:
    """Expose ``request.user`` (when authenticated) to audit helpers during HTTP handling."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> Any:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            _ctx.user = user
        else:
            _ctx.user = None
        try:
            return self.get_response(request)
        finally:
            _ctx.user = None
