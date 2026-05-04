"""Audit event service.

The service records operational events through repository interfaces and keeps
secrets out of audit payloads.
"""

from typing import Any, Optional
from uuid import uuid4

from app.repositories import AuditEventRecord, RepositoryBundle, get_repository_bundle

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "service_role",
    "supabase_key",
    "token",
)


def sanitize_audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of payload with sensitive values redacted."""

    def sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "***" if _is_sensitive_key(key) else sanitize(nested)
                for key, nested in value.items()
            }
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    return sanitize(payload)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


class AuditService:
    """Record runtime and integration events through audit repositories."""

    def __init__(self, repositories: Optional[RepositoryBundle] = None):
        self.repositories = repositories or get_repository_bundle()

    def record_event(
        self,
        event_type: str,
        *,
        actor_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> AuditEventRecord:
        """Persist a sanitized audit event."""
        record = AuditEventRecord(
            id=str(uuid4()),
            event_type=event_type,
            actor_id=actor_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload=sanitize_audit_payload(payload or {}),
        )
        return self.repositories.audit_logs.record_event(record)

    def agent_turn_started(self, *, agent_id: str, conversation_id: str) -> AuditEventRecord:
        return self.record_event(
            "agent.turn.started",
            agent_id=agent_id,
            conversation_id=conversation_id,
        )

    def agent_turn_completed(
        self,
        *,
        agent_id: str,
        conversation_id: str,
        success: bool,
        execution_time_ms: float,
        error: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.record_event(
            "agent.turn.completed",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={
                "success": success,
                "execution_time_ms": execution_time_ms,
                "error": error,
            },
        )

    def model_call_blocked(
        self,
        *,
        agent_id: str,
        conversation_id: str,
        reason: str,
    ) -> AuditEventRecord:
        return self.record_event(
            "model.call.blocked",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={"reason": reason},
        )

    def loop_detected(
        self,
        *,
        agent_id: str,
        conversation_id: str,
        reason: str,
    ) -> AuditEventRecord:
        return self.record_event(
            "loop.detected",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={"reason": reason},
        )

    def timeout(
        self,
        *,
        agent_id: str,
        conversation_id: str,
        timeout_seconds: int,
    ) -> AuditEventRecord:
        return self.record_event(
            "agent.timeout",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={"timeout_seconds": timeout_seconds},
        )

    def tool_call_started(
        self,
        *,
        skill_name: str,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.record_event(
            "tool.call.started",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={"skill_name": skill_name},
        )

    def tool_call_completed(
        self,
        *,
        skill_name: str,
        success: bool,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.record_event(
            "tool.call.completed",
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload={"skill_name": skill_name, "success": success, "error": error},
        )

    def webhook_rejected(
        self,
        *,
        reason: str,
        actor_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AuditEventRecord:
        return self.record_event(
            "webhook.rejected",
            actor_id=actor_id,
            conversation_id=conversation_id,
            payload={"reason": reason},
        )
