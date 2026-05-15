"""ORM hooks that complement explicit audit writes — Step 7.2.

``QuerySet.update()`` bypasses ``save()`` and thus these receivers; those code paths
call ``write_audit_log`` directly.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models.approval import ApprovalRequest
from app.services.audit.log import write_audit_log


@receiver(post_save, sender=ApprovalRequest)
def audit_approval_request_created(
    sender, instance: ApprovalRequest, created: bool, **kwargs
) -> None:
    if not created:
        return
    write_audit_log(
        actor=None,
        action="approval.request_created",
        resource_type="workflow",
        resource_id=str(instance.workflow_id),
        before_json=None,
        after_json={
            "workflow_id": int(instance.workflow_id),
            "approval_request_id": int(instance.pk),
            "status": str(instance.status),
        },
        token_usage=None,
    )
