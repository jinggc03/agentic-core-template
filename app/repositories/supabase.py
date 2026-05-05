"""Supabase-backed repository implementations."""

from typing import Any, Optional, TypeVar

from app.integrations.supabase.client import get_supabase_service_client
from app.repositories.base import (
    AgentStateRecord,
    AuditEventRecord,
    ConversationRecord,
    FileRecord,
    MessageRecord,
    RepositoryBundle,
    SkillRunRecord,
)

RecordT = TypeVar(
    "RecordT",
    ConversationRecord,
    MessageRecord,
    AgentStateRecord,
    SkillRunRecord,
    AuditEventRecord,
    FileRecord,
)


def _record_to_row(record: RecordT) -> dict[str, Any]:
    """Serialize repository records into Supabase-compatible JSON rows."""
    return record.model_dump(mode="json")


def _response_data(response: Any) -> Any:
    return getattr(response, "data", response)


def _first(response: Any) -> Optional[dict[str, Any]]:
    data = _response_data(response)
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict):
        return data
    return None


def _list(response: Any) -> list[dict[str, Any]]:
    data = _response_data(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


class _SupabaseRepository:
    """Shared Supabase table helpers."""

    table_name: str

    def __init__(self, client: Any):
        self.client = client

    def _table(self) -> Any:
        return self.client.table(self.table_name)


class SupabaseConversationRepository(_SupabaseRepository):
    """Supabase implementation for conversation metadata."""

    table_name = "conversations"

    def create_conversation(self, record: ConversationRecord) -> ConversationRecord:
        row = _first(self._table().insert(_record_to_row(record)).execute())
        return ConversationRecord.model_validate(row or _record_to_row(record))

    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        row = _first(self._table().select("*").eq("id", conversation_id).limit(1).execute())
        return ConversationRecord.model_validate(row) if row else None

    def list_conversations(
        self,
        *,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[ConversationRecord]:
        query = self._table().select("*")
        if agent_id is not None:
            query = query.eq("agent_id", agent_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        return [ConversationRecord.model_validate(row) for row in _list(query.execute())]


class SupabaseMessageRepository(_SupabaseRepository):
    """Supabase implementation for conversation messages."""

    table_name = "messages"

    def add_message(self, record: MessageRecord) -> MessageRecord:
        row = _first(self._table().insert(_record_to_row(record)).execute())
        return MessageRecord.model_validate(row or _record_to_row(record))

    def list_messages(self, conversation_id: str) -> list[MessageRecord]:
        response = (
            self._table()
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .execute()
        )
        return [MessageRecord.model_validate(row) for row in _list(response)]


class SupabaseAgentStateRepository(_SupabaseRepository):
    """Supabase implementation for agent snapshots."""

    table_name = "agent_snapshots"

    def save_state(self, record: AgentStateRecord) -> AgentStateRecord:
        row = _first(
            self._table()
            .upsert(_record_to_row(record), on_conflict="agent_id,conversation_id")
            .execute()
        )
        return AgentStateRecord.model_validate(row or _record_to_row(record))

    def get_state(self, agent_id: str, conversation_id: str) -> Optional[AgentStateRecord]:
        row = _first(
            self._table()
            .select("*")
            .eq("agent_id", agent_id)
            .eq("conversation_id", conversation_id)
            .limit(1)
            .execute()
        )
        return AgentStateRecord.model_validate(row) if row else None


class SupabaseSkillRunRepository(_SupabaseRepository):
    """Supabase implementation for skill execution records."""

    table_name = "skill_runs"

    def record_skill_run(self, record: SkillRunRecord) -> SkillRunRecord:
        row = _first(self._table().insert(_record_to_row(record)).execute())
        return SkillRunRecord.model_validate(row or _record_to_row(record))

    def list_skill_runs(
        self,
        *,
        conversation_id: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> list[SkillRunRecord]:
        query = self._table().select("*")
        if conversation_id is not None:
            query = query.eq("conversation_id", conversation_id)
        if skill_name is not None:
            query = query.eq("skill_name", skill_name)
        return [SkillRunRecord.model_validate(row) for row in _list(query.execute())]


class SupabaseAuditLogRepository(_SupabaseRepository):
    """Supabase implementation for audit events."""

    table_name = "audit_events"

    def record_event(self, record: AuditEventRecord) -> AuditEventRecord:
        row = _first(self._table().insert(_record_to_row(record)).execute())
        return AuditEventRecord.model_validate(row or _record_to_row(record))

    def list_events(
        self,
        *,
        conversation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]:
        query = self._table().select("*")
        if conversation_id is not None:
            query = query.eq("conversation_id", conversation_id)
        if event_type is not None:
            query = query.eq("event_type", event_type)
        response = query.order("created_at", desc=True).limit(limit).execute()
        return [AuditEventRecord.model_validate(row) for row in _list(response)]


class SupabaseFileRepository(_SupabaseRepository):
    """Supabase implementation for file metadata."""

    table_name = "files"

    def save_file_record(self, record: FileRecord) -> FileRecord:
        row = _first(self._table().upsert(_record_to_row(record), on_conflict="id").execute())
        return FileRecord.model_validate(row or _record_to_row(record))

    def get_file_record(self, file_id: str) -> Optional[FileRecord]:
        row = _first(self._table().select("*").eq("id", file_id).limit(1).execute())
        return FileRecord.model_validate(row) if row else None

    def list_files(
        self,
        *,
        owner_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> list[FileRecord]:
        query = self._table().select("*")
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)
        if conversation_id is not None:
            query = query.eq("conversation_id", conversation_id)
        return [FileRecord.model_validate(row) for row in _list(query.execute())]


def create_supabase_repository_bundle(client: Any | None = None) -> RepositoryBundle:
    """Create a repository bundle backed by Supabase tables."""
    resolved_client = client or get_supabase_service_client()
    return RepositoryBundle(
        conversations=SupabaseConversationRepository(resolved_client),
        messages=SupabaseMessageRepository(resolved_client),
        agent_states=SupabaseAgentStateRepository(resolved_client),
        skill_runs=SupabaseSkillRunRepository(resolved_client),
        audit_logs=SupabaseAuditLogRepository(resolved_client),
        files=SupabaseFileRepository(resolved_client),
    )
