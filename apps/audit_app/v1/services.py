from typing import Any, Dict, Optional

from common.enums import AuditAction
from common.utils import normalize_value

from .models import AuditLog

# ------------------------------
# HELPERS
# ------------------------------


def normalize_changes(changes: Optional[Dict[str, Any]]):
    """Normalize diff values safely."""
    if not changes:
        return {}
    return {
        field: {
            "old": normalize_value(diff.get("old")),
            "new": normalize_value(diff.get("new")),
        }
        for field, diff in changes.items()
    }


def build_payload(
    *,
    action: str,
    target_model: str,
    target_object_id: str,
    object_representation: str,
    trace_id: str,
    actor_id: Optional[str],
    actor_email: Optional[str],
    correlation_id: Optional[str],
    session_key: Optional[str],
    ip_address: Optional[str],
    user_agent: Optional[str],
    changes: Dict[str, Any],
):
    """Centralized payload builder — NO Django model objects."""
    return {
        "action": normalize_value(action),
        "target_model": normalize_value(target_model),
        "target_object_id": normalize_value(target_object_id),
        "object_representation": normalize_value(object_representation),
        "trace_id": normalize_value(trace_id),
        "actor_id": normalize_value(actor_id),
        "actor_email": normalize_value(actor_email),
        "correlation_id": normalize_value(correlation_id),
        "session_key": normalize_value(session_key),
        "ip_address": normalize_value(ip_address),
        "user_agent": normalize_value(user_agent),
        "changes": normalize_changes(changes),
    }


class AuditService:

    # ------------------------------
    # LOW-LEVEL WRITERS
    # ------------------------------

    @staticmethod
    async def write_async(payload: Dict[str, Any]) -> AuditLog:
        return await AuditLog.objects.acreate(**payload)

    @staticmethod
    def write_sync(payload: Dict[str, Any]) -> AuditLog:
        return AuditLog.objects.create(**payload)

    # ------------------------------
    # PUBLIC METHODS (Async)
    # ------------------------------

    @classmethod
    async def log_async(cls, *, action: str, **payload_fields):
        payload = build_payload(action=action, **payload_fields)
        return await cls.write_async(payload)

    @classmethod
    async def log_create(cls, **payload_fields):
        return await cls.log_async(action=AuditAction.CREATE, **payload_fields)

    @classmethod
    async def log_update(cls, **payload_fields):
        return await cls.log_async(action=AuditAction.UPDATE, **payload_fields)

    @classmethod
    async def log_delete(cls, **payload_fields):
        return await cls.log_async(action=AuditAction.DELETE, **payload_fields)

    # ------------------------------
    # PUBLIC METHODS (Sync)
    # ------------------------------

    @classmethod
    def log_sync(cls, *, action: str, **payload_fields):
        payload = build_payload(action=action, **payload_fields)
        return cls.write_sync(payload)

    @classmethod
    def log_create_sync(cls, **payload_fields):
        return cls.log_sync(action=AuditAction.CREATE, **payload_fields)

    @classmethod
    def log_update_sync(cls, **payload_fields):
        return cls.log_sync(action=AuditAction.UPDATE, **payload_fields)

    @classmethod
    def log_delete_sync(cls, **payload_fields):
        return cls.log_sync(action=AuditAction.DELETE, **payload_fields)
