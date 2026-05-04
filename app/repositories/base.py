"""Infrastructure-neutral repository contracts.

Agents and skills should depend on these interfaces instead of concrete storage
implementations. Supabase support is added behind these contracts in later cards.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class RepositoryRecord(BaseModel):
    """Base model for repository records."""

    model_config = ConfigDict(extra="forbid")


class ConversationRecord(RepositoryRecord):
    """Conversation metadata for an agent session."""

    id: str
    agent_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MessageRecord(RepositoryRecord):
    """Persisted message in a conversation."""

    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AgentStateRecord(RepositoryRecord):
    """Latest state/snapshot for an agent conversation."""

    id: str
    agent_id: str
    conversation_id: str
    state: dict[str, Any] = Field(default_factory=dict)
    snapshot: Optional[dict[str, Any]] = None
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SkillRunRecord(RepositoryRecord):
    """Recorded skill execution."""

    id: str
    skill_name: str
    conversation_id: Optional[str] = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[dict[str, Any]] = None
    status: str = "success"
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AuditEventRecord(RepositoryRecord):
    """Audit event emitted by runtime or integrations."""

    id: str
    event_type: str
    actor_id: Optional[str] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class FileRecord(RepositoryRecord):
    """Metadata for a file managed by storage infrastructure."""

    id: str
    bucket: str
    path: str
    owner_id: Optional[str] = None
    conversation_id: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


@runtime_checkable
class ConversationRepository(Protocol):
    """Repository for conversation metadata."""

    def create_conversation(self, record: ConversationRecord) -> ConversationRecord: ...

    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]: ...

    def list_conversations(
        self,
        *,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[ConversationRecord]: ...


@runtime_checkable
class MessageRepository(Protocol):
    """Repository for conversation messages."""

    def add_message(self, record: MessageRecord) -> MessageRecord: ...

    def list_messages(self, conversation_id: str) -> list[MessageRecord]: ...


@runtime_checkable
class AgentStateRepository(Protocol):
    """Repository for agent state and snapshots."""

    def save_state(self, record: AgentStateRecord) -> AgentStateRecord: ...

    def get_state(self, agent_id: str, conversation_id: str) -> Optional[AgentStateRecord]: ...


@runtime_checkable
class SkillRunRepository(Protocol):
    """Repository for skill execution records."""

    def record_skill_run(self, record: SkillRunRecord) -> SkillRunRecord: ...

    def list_skill_runs(
        self,
        *,
        conversation_id: Optional[str] = None,
        skill_name: Optional[str] = None,
    ) -> list[SkillRunRecord]: ...


@runtime_checkable
class AuditLogRepository(Protocol):
    """Repository for runtime audit events."""

    def record_event(self, record: AuditEventRecord) -> AuditEventRecord: ...

    def list_events(
        self,
        *,
        conversation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]: ...


@runtime_checkable
class FileRepository(Protocol):
    """Repository for storage file metadata."""

    def save_file_record(self, record: FileRecord) -> FileRecord: ...

    def get_file_record(self, file_id: str) -> Optional[FileRecord]: ...

    def list_files(
        self,
        *,
        owner_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> list[FileRecord]: ...


@dataclass(frozen=True)
class RepositoryBundle:
    """Container for repository dependencies."""

    conversations: ConversationRepository
    messages: MessageRepository
    agent_states: AgentStateRepository
    skill_runs: SkillRunRepository
    audit_logs: AuditLogRepository
    files: FileRepository
