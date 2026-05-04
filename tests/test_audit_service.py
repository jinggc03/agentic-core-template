"""Tests for audit event service."""

from app.repositories import create_memory_repository_bundle
from app.services.audit import AuditService, sanitize_audit_payload


def test_audit_service_records_turn_and_policy_events():
    bundle = create_memory_repository_bundle()
    service = AuditService(repositories=bundle)

    service.agent_turn_started(agent_id="agent-1", conversation_id="conv-1")
    service.agent_turn_completed(
        agent_id="agent-1",
        conversation_id="conv-1",
        success=True,
        execution_time_ms=12.5,
    )
    service.model_call_blocked(agent_id="agent-1", conversation_id="conv-1", reason="limit")

    events = bundle.audit_logs.list_events(conversation_id="conv-1")

    assert [event.event_type for event in events] == [
        "agent.turn.started",
        "agent.turn.completed",
        "model.call.blocked",
    ]
    assert events[1].payload["success"] is True


def test_sanitize_audit_payload_redacts_nested_sensitive_values():
    payload = sanitize_audit_payload(
        {
            "safe": "value",
            "api_key": "secret",
            "nested": {"authorization": "Bearer token", "items": [{"password": "pw"}]},
        }
    )

    assert payload["safe"] == "value"
    assert payload["api_key"] == "***"
    assert payload["nested"]["authorization"] == "***"
    assert payload["nested"]["items"][0]["password"] == "***"
