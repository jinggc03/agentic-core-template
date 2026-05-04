"""Tests for in-memory repository implementations and factory selection."""

import pytest

from app.core.config import Settings
from app.repositories import (
    AgentStateRecord,
    AuditEventRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
    RepositoryBundle,
    SkillRunRecord,
    create_memory_repository_bundle,
    get_repository_bundle,
    reset_repository_bundle,
)
from app.repositories.factory import RepositoryConfigurationError


@pytest.fixture(autouse=True)
def reset_bundle():
    reset_repository_bundle()
    yield
    reset_repository_bundle()


def test_memory_repositories_round_trip_core_records():
    bundle = create_memory_repository_bundle()

    conversation = bundle.conversations.create_conversation(
        ConversationRecord(id="conv-1", agent_id="invoice-agent", user_id="user-1")
    )
    message = bundle.messages.add_message(
        MessageRecord(id="msg-1", conversation_id="conv-1", role="user", content="hello")
    )
    state = bundle.agent_states.save_state(
        AgentStateRecord(
            id="state-1",
            agent_id="invoice-agent",
            conversation_id="conv-1",
            state={"stage": "started"},
        )
    )
    skill_run = bundle.skill_runs.record_skill_run(
        SkillRunRecord(
            id="skill-1",
            skill_name="calculator",
            conversation_id="conv-1",
            input_data={"expression": "2+2"},
            output_data={"result": 4},
        )
    )
    audit_event = bundle.audit_logs.record_event(
        AuditEventRecord(
            id="audit-1",
            event_type="agent.turn.completed",
            conversation_id="conv-1",
            payload={"success": True},
        )
    )
    file_record = bundle.files.save_file_record(
        FileRecord(
            id="file-1",
            bucket="agent-files",
            path="conv-1/input.pdf",
            owner_id="user-1",
            conversation_id="conv-1",
        )
    )

    assert bundle.conversations.get_conversation("conv-1") == conversation
    assert bundle.messages.list_messages("conv-1") == [message]
    assert bundle.agent_states.get_state("invoice-agent", "conv-1") == state
    assert bundle.skill_runs.list_skill_runs(conversation_id="conv-1") == [skill_run]
    assert bundle.audit_logs.list_events(conversation_id="conv-1") == [audit_event]
    assert bundle.files.get_file_record("file-1") == file_record


def test_memory_repositories_filter_records():
    bundle = create_memory_repository_bundle()

    bundle.conversations.create_conversation(
        ConversationRecord(id="conv-1", agent_id="agent-a", user_id="user-1")
    )
    bundle.conversations.create_conversation(
        ConversationRecord(id="conv-2", agent_id="agent-b", user_id="user-2")
    )
    bundle.skill_runs.record_skill_run(SkillRunRecord(id="skill-1", skill_name="calculator"))
    bundle.skill_runs.record_skill_run(SkillRunRecord(id="skill-2", skill_name="text"))
    bundle.audit_logs.record_event(AuditEventRecord(id="audit-1", event_type="a"))
    bundle.audit_logs.record_event(AuditEventRecord(id="audit-2", event_type="b"))
    bundle.files.save_file_record(
        FileRecord(id="file-1", bucket="agent-files", path="a.txt", owner_id="user-1")
    )
    bundle.files.save_file_record(
        FileRecord(id="file-2", bucket="agent-files", path="b.txt", owner_id="user-2")
    )

    assert [record.id for record in bundle.conversations.list_conversations(agent_id="agent-a")] == [
        "conv-1"
    ]
    assert [record.id for record in bundle.skill_runs.list_skill_runs(skill_name="calculator")] == [
        "skill-1"
    ]
    assert [record.id for record in bundle.audit_logs.list_events(event_type="b")] == ["audit-2"]
    assert [record.id for record in bundle.files.list_files(owner_id="user-2")] == ["file-2"]


def test_repository_factory_defaults_to_memory_when_supabase_disabled():
    settings = Settings(SUPABASE_ENABLED=False)

    bundle = get_repository_bundle(settings=settings)

    assert isinstance(bundle, RepositoryBundle)
    conversation = bundle.conversations.create_conversation(
        ConversationRecord(id="conv-1", agent_id="agent-1")
    )
    assert bundle.conversations.get_conversation("conv-1") == conversation


def test_repository_factory_caches_default_bundle(monkeypatch):
    monkeypatch.setattr(
        "app.repositories.factory._get_settings",
        lambda: Settings(SUPABASE_ENABLED=False),
    )

    first = get_repository_bundle()
    second = get_repository_bundle()

    assert first is second


def test_repository_factory_rejects_supabase_until_implementation_exists():
    settings = Settings(
        SUPABASE_ENABLED=True,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_ANON_KEY="anon-key",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
    )

    with pytest.raises(RepositoryConfigurationError, match="Supabase repositories are not implemented"):
        get_repository_bundle(settings=settings)
