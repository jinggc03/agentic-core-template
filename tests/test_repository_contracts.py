"""Tests for infrastructure-neutral repository contracts."""

from typing import Optional

from app.repositories import (
    AgentStateRecord,
    AgentStateRepository,
    AuditEventRecord,
    AuditLogRepository,
    ConversationRecord,
    ConversationRepository,
    FileRecord,
    FileRepository,
    MessageRecord,
    MessageRepository,
    RepositoryBundle,
    SkillRunRecord,
    SkillRunRepository,
)


class FakeConversationRepository:
    def __init__(self):
        self.records: dict[str, ConversationRecord] = {}

    def create_conversation(self, record: ConversationRecord) -> ConversationRecord:
        self.records[record.id] = record
        return record

    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        return self.records.get(conversation_id)

    def list_conversations(
        self,
        *,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[ConversationRecord]:
        records = list(self.records.values())
        if agent_id is not None:
            records = [record for record in records if record.agent_id == agent_id]
        if user_id is not None:
            records = [record for record in records if record.user_id == user_id]
        return records


class FakeMessageRepository:
    def __init__(self):
        self.records: list[MessageRecord] = []

    def add_message(self, record: MessageRecord) -> MessageRecord:
        self.records.append(record)
        return record

    def list_messages(self, conversation_id: str) -> list[MessageRecord]:
        return [record for record in self.records if record.conversation_id == conversation_id]


class FakeAgentStateRepository:
    def __init__(self):
        self.records: dict[tuple[str, str], AgentStateRecord] = {}

    def save_state(self, record: AgentStateRecord) -> AgentStateRecord:
        self.records[(record.agent_id, record.conversation_id)] = record
        return record

    def get_state(self, agent_id: str, conversation_id: str) -> Optional[AgentStateRecord]:
        return self.records.get((agent_id, conversation_id))


class FakeSkillRunRepository:
    def __init__(self):
        self.records: list[SkillRunRecord] = []

    def record_skill_run(self, record: SkillRunRecord) -> SkillRunRecord:
        self.records.append(record)
        return record

    def list_skill_runs(
        self,
        *,
        conversation_id: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> list[SkillRunRecord]:
        records = self.records
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        if skill_name is not None:
            records = [record for record in records if record.skill_name == skill_name]
        return records


class FakeAuditLogRepository:
    def __init__(self):
        self.records: list[AuditEventRecord] = []

    def record_event(self, record: AuditEventRecord) -> AuditEventRecord:
        self.records.append(record)
        return record

    def list_events(
        self,
        *,
        conversation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]:
        records = self.records
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        if event_type is not None:
            records = [record for record in records if record.event_type == event_type]
        return records[:limit]


class FakeFileRepository:
    def __init__(self):
        self.records: dict[str, FileRecord] = {}

    def save_file_record(self, record: FileRecord) -> FileRecord:
        self.records[record.id] = record
        return record

    def get_file_record(self, file_id: str) -> Optional[FileRecord]:
        return self.records.get(file_id)

    def list_files(
        self,
        *,
        owner_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> list[FileRecord]:
        records = list(self.records.values())
        if owner_id is not None:
            records = [record for record in records if record.owner_id == owner_id]
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        return records


def test_repository_protocols_accept_fake_implementations():
    conversations = FakeConversationRepository()
    messages = FakeMessageRepository()
    agent_states = FakeAgentStateRepository()
    skill_runs = FakeSkillRunRepository()
    audit_logs = FakeAuditLogRepository()
    files = FakeFileRepository()

    assert isinstance(conversations, ConversationRepository)
    assert isinstance(messages, MessageRepository)
    assert isinstance(agent_states, AgentStateRepository)
    assert isinstance(skill_runs, SkillRunRepository)
    assert isinstance(audit_logs, AuditLogRepository)
    assert isinstance(files, FileRepository)


def test_repository_bundle_groups_contracts():
    bundle = RepositoryBundle(
        conversations=FakeConversationRepository(),
        messages=FakeMessageRepository(),
        agent_states=FakeAgentStateRepository(),
        skill_runs=FakeSkillRunRepository(),
        audit_logs=FakeAuditLogRepository(),
        files=FakeFileRepository(),
    )

    conversation = bundle.conversations.create_conversation(
        ConversationRecord(id="conv-1", agent_id="invoice-agent", user_id="user-1")
    )
    message = bundle.messages.add_message(
        MessageRecord(id="msg-1", conversation_id="conv-1", role="user", content="hello")
    )
    state = bundle.agent_states.save_state(
        AgentStateRecord(id="state-1", agent_id="invoice-agent", conversation_id="conv-1")
    )
    skill_run = bundle.skill_runs.record_skill_run(
        SkillRunRecord(id="skill-1", skill_name="calculator", conversation_id="conv-1")
    )
    audit_event = bundle.audit_logs.record_event(
        AuditEventRecord(id="audit-1", event_type="agent.turn.completed", conversation_id="conv-1")
    )
    file_record = bundle.files.save_file_record(
        FileRecord(id="file-1", bucket="agent-files", path="conv-1/input.pdf")
    )

    assert conversation.id == "conv-1"
    assert message.role == "user"
    assert state.version == 1
    assert skill_run.status == "success"
    assert audit_event.payload == {}
    assert file_record.bucket == "agent-files"


def test_repository_records_are_pydantic_models_with_safe_defaults():
    conversation = ConversationRecord(id="conv-1", agent_id="agent-1")
    skill_run = SkillRunRecord(id="skill-1", skill_name="calculator")

    dumped = conversation.model_dump()

    assert dumped["metadata"] == {}
    assert conversation.created_at.tzinfo is not None
    assert skill_run.input_data == {}
    assert skill_run.status == "success"
