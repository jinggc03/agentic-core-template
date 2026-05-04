"""Optional integration tests for real/local Supabase repositories.

Run with:
    SUPABASE_TESTS=true SUPABASE_ENABLED=true python -m pytest tests/integration -q
"""

import os
from uuid import uuid4

import pytest

from app.repositories import (
    AgentStateRecord,
    AuditEventRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
)
from app.repositories.supabase import create_supabase_repository_bundle

pytestmark = pytest.mark.skipif(
    os.getenv("SUPABASE_TESTS") != "true",
    reason="Supabase integration tests are opt-in. Set SUPABASE_TESTS=true.",
)


def test_supabase_repository_round_trip_against_real_project():
    bundle = create_supabase_repository_bundle()
    suffix = uuid4().hex
    conversation_id = f"it-conv-{suffix}"
    message_id = f"it-msg-{suffix}"
    state_id = f"it-state-{suffix}"
    audit_id = f"it-audit-{suffix}"
    file_id = f"it-file-{suffix}"

    conversation = bundle.conversations.create_conversation(
        ConversationRecord(id=conversation_id, agent_id="integration-agent", user_id=None)
    )
    message = bundle.messages.add_message(
        MessageRecord(
            id=message_id,
            conversation_id=conversation_id,
            role="user",
            content="integration test",
        )
    )
    state = bundle.agent_states.save_state(
        AgentStateRecord(
            id=state_id,
            agent_id="integration-agent",
            conversation_id=conversation_id,
            state={"test": True},
        )
    )
    audit_event = bundle.audit_logs.record_event(
        AuditEventRecord(
            id=audit_id,
            event_type="integration.test",
            conversation_id=conversation_id,
            payload={"ok": True},
        )
    )
    file_record = bundle.files.save_file_record(
        FileRecord(
            id=file_id,
            bucket="agent-files",
            path=f"integration/{suffix}.txt",
            conversation_id=conversation_id,
        )
    )

    assert bundle.conversations.get_conversation(conversation_id) == conversation
    assert bundle.messages.list_messages(conversation_id) == [message]
    assert bundle.agent_states.get_state("integration-agent", conversation_id) == state
    assert bundle.audit_logs.list_events(conversation_id=conversation_id) == [audit_event]
    assert bundle.files.list_files(conversation_id=conversation_id) == [file_record]
