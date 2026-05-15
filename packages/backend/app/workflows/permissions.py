"""RBAC for workflow-related endpoints — Step 7.2 audit logs."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from app.accounts.models import User


class IsManager(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", None) == User.Role.MANAGER)
