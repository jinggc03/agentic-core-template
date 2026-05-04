"""In-memory repository implementations.

These repositories are the default when Supabase is disabled. They keep the
template runnable without external infrastructure and provide useful fakes for
tests.
"""

from typing import Optional

from app.repositories.base import (
    AgentStateRecord,
    AuditEventRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
    RepositoryBundle,
    SkillRunRecord,
)


class InMemoryConversationRepository:
    """In-memory conversation repository."""

    def __init__(self):
        self._records: dict[str, ConversationRecord] = {}

    def create_conversation(self, record: ConversationRecord) -> ConversationRecord:
        self._records[record.id] = record
        return record

    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        return self._records.get(conversation_id)

    def list_conversations(
        self,
        *,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[ConversationRecord]:
        records = list(self._records.values())
        if agent_id is not None:
            records = [record for record in records if record.agent_id == agent_id]
        if user_id is not None:
            records = [record for record in records if record.user_id == user_id]
        return records


class InMemoryMessageRepository:
    """In-memory message repository."""

    def __init__(self):
        self._records: list[MessageRecord] = []

    def add_message(self, record: MessageRecord) -> MessageRecord:
        self._records.append(record)
        return record

    def list_messages(self, conversation_id: str) -> list[MessageRecord]:
        return [record for record in self._records if record.conversation_id == conversation_id]


class InMemoryAgentStateRepository:
    """In-memory agent state repository."""

    def __init__(self):
        self._records: dict[tuple[str, str], AgentStateRecord] = {}

    def save_state(self, record: AgentStateRecord) -> AgentStateRecord:
        self._records[(record.agent_id, record.conversation_id)] = record
        return record

    def get_state(self, agent_id: str, conversation_id: str) -> Optional[AgentStateRecord]:
        return self._records.get((agent_id, conversation_id))


class InMemorySkillRunRepository:
    """In-memory skill run repository."""

    def __init__(self):
        self._records: list[SkillRunRecord] = []

    def record_skill_run(self, record: SkillRunRecord) -> SkillRunRecord:
        self._records.append(record)
        return record

    def list_skill_runs(
        self,
        *,
        conversation_id: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> list[SkillRunRecord]:
        records = self._records
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        if skill_name is not None:
            records = [record for record in records if record.skill_name == skill_name]
        return list(records)


class InMemoryAuditLogRepository:
    """In-memory audit log repository."""

    def __init__(self):
        self._records: list[AuditEventRecord] = []

    def record_event(self, record: AuditEventRecord) -> AuditEventRecord:
        self._records.append(record)
        return record

    def list_events(
        self,
        *,
        conversation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]:
        records = self._records
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        if event_type is not None:
            records = [record for record in records if record.event_type == event_type]
        return list(records[:limit])


class InMemoryFileRepository:
    """In-memory file metadata repository."""

    def __init__(self):
        self._records: dict[str, FileRecord] = {}

    def save_file_record(self, record: FileRecord) -> FileRecord:
        self._records[record.id] = record
        return record

    def get_file_record(self, file_id: str) -> Optional[FileRecord]:
        return self._records.get(file_id)

    def list_files(
        self,
        *,
        owner_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> list[FileRecord]:
        records = list(self._records.values())
        if owner_id is not None:
            records = [record for record in records if record.owner_id == owner_id]
        if conversation_id is not None:
            records = [record for record in records if record.conversation_id == conversation_id]
        return records


def create_memory_repository_bundle() -> RepositoryBundle:
    """Create a fresh in-memory repository bundle."""
    return RepositoryBundle(
        conversations=InMemoryConversationRepository(),
        messages=InMemoryMessageRepository(),
        agent_states=InMemoryAgentStateRepository(),
        skill_runs=InMemorySkillRunRepository(),
        audit_logs=InMemoryAuditLogRepository(),
        files=InMemoryFileRepository(),
    )
