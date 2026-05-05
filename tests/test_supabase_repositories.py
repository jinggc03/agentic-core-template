"""Tests for Supabase-backed repository adapters using a fake client."""

from app.core.config import Settings
from app.repositories import (
    AgentStateRecord,
    AuditEventRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
    SkillRunRecord,
)
from app.repositories.factory import get_repository_bundle, reset_repository_bundle
from app.repositories.supabase import create_supabase_repository_bundle


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.limit_value = None
        self.payload = None
        self.mode = "select"

    def select(self, *_args):
        self.mode = "select"
        return self

    def insert(self, payload):
        self.mode = "insert"
        self.payload = payload
        return self

    def upsert(self, payload, **_kwargs):
        self.mode = "upsert"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, limit):
        self.limit_value = limit
        return self

    def execute(self):
        table = self.client.tables.setdefault(self.table_name, [])
        if self.mode == "insert":
            table.append(dict(self.payload))
            return FakeResponse([dict(self.payload)])
        if self.mode == "upsert":
            payload = dict(self.payload)
            existing = next((row for row in table if row.get("id") == payload.get("id")), None)
            if existing is None:
                table.append(payload)
            else:
                existing.update(payload)
                payload = existing
            return FakeResponse([dict(payload)])

        rows = [
            dict(row)
            for row in table
            if all(row.get(field) == value for field, value in self.filters)
        ]
        if self.limit_value is not None:
            rows = rows[: self.limit_value]
        return FakeResponse(rows)


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {}

    def table(self, table_name):
        return FakeQuery(self, table_name)


def test_supabase_repositories_round_trip_records():
    bundle = create_supabase_repository_bundle(client=FakeSupabaseClient())

    conversation = bundle.conversations.create_conversation(
        ConversationRecord(id="conv-1", agent_id="agent-1", user_id="user-1")
    )
    message = bundle.messages.add_message(
        MessageRecord(id="msg-1", conversation_id="conv-1", role="user", content="hello")
    )
    state = bundle.agent_states.save_state(
        AgentStateRecord(
            id="state-1",
            agent_id="agent-1",
            conversation_id="conv-1",
            state={"turn": 1},
        )
    )
    skill_run = bundle.skill_runs.record_skill_run(
        SkillRunRecord(id="skill-1", skill_name="calculator", conversation_id="conv-1")
    )
    audit_event = bundle.audit_logs.record_event(
        AuditEventRecord(id="audit-1", event_type="agent.turn.completed", conversation_id="conv-1")
    )
    file_record = bundle.files.save_file_record(
        FileRecord(id="file-1", bucket="agent-files", path="conv-1/input.pdf", owner_id="user-1")
    )

    assert bundle.conversations.get_conversation("conv-1") == conversation
    assert bundle.messages.list_messages("conv-1") == [message]
    assert bundle.agent_states.get_state("agent-1", "conv-1") == state
    assert bundle.skill_runs.list_skill_runs(conversation_id="conv-1") == [skill_run]
    assert bundle.audit_logs.list_events(conversation_id="conv-1") == [audit_event]
    assert bundle.files.get_file_record("file-1") == file_record


def test_repository_factory_can_select_supabase_bundle(monkeypatch):
    reset_repository_bundle()
    expected_bundle = create_supabase_repository_bundle(client=FakeSupabaseClient())
    settings = Settings(
        SUPABASE_ENABLED=True,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_ANON_KEY="anon-key",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
    )

    monkeypatch.setattr(
        "app.repositories.supabase.create_supabase_repository_bundle",
        lambda: expected_bundle,
    )

    try:
        assert get_repository_bundle(settings=settings) is expected_bundle
    finally:
        reset_repository_bundle()
