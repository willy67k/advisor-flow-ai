"""Persist structured audit events — Step 7.2."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser

from app.models.audit_log import AuditLog
from app.models.workflow import Workflow


def workflow_audit_snapshot(wf: Workflow) -> dict[str, Any]:
    return {
        "workflow_id": int(wf.pk),
        "meeting_id": int(wf.meeting_id),
        "status": str(wf.status),
        "celery_task_id": str(wf.celery_task_id or ""),
        "result_json": wf.result_json,
    }


def write_audit_log(
    *,
    actor: AbstractBaseUser | None,
    action: str,
    resource_type: str,
    resource_id: str,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    token_usage: dict[str, Any] | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        actor_id=getattr(actor, "pk", None) if actor is not None else None,
        action=str(action),
        resource_type=str(resource_type),
        resource_id=str(resource_id),
        before_json=before_json,
        after_json=after_json,
        token_usage=token_usage,
    )


__all__ = ["workflow_audit_snapshot", "write_audit_log"]
