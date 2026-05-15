"""RBAC for workflow-related endpoints — Step 7.2 audit logs."""

from __future__ import annotations

from app.accounts.permissions import IsManager

__all__ = ["IsManager"]
