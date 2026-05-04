"""Infrastructure-neutral knowledge layer contracts."""

from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class RAGConfigurationError(RuntimeError):
    """Raised when RAG is requested but cannot be configured."""


class KnowledgeRecord(BaseModel):
    """Base model for knowledge records."""

    model_config = ConfigDict(extra="forbid")


class KnowledgeDocumentRecord(KnowledgeRecord):
    """Metadata for an ingested knowledge document."""

    id: str
    owner_id: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeChunkRecord(KnowledgeRecord):
    """A searchable chunk of a knowledge document."""

    id: str
    document_id: str
    owner_id: Optional[str] = None
    content: str
    chunk_index: int
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeSearchMatch(KnowledgeRecord):
    """A retrieved knowledge chunk with similarity metadata."""

    document_id: str
    chunk_id: str
    content: str
    similarity: float
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider contract for text embeddings."""

    model: str
    dimensions: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class KnowledgeRepository(Protocol):
    """Repository contract for vector-backed knowledge retrieval."""

    def save_document(self, record: KnowledgeDocumentRecord) -> KnowledgeDocumentRecord: ...

    def save_chunks(self, records: list[KnowledgeChunkRecord]) -> list[KnowledgeChunkRecord]: ...

    def search_chunks(
        self,
        *,
        query_embedding: list[float],
        owner_id: Optional[str] = None,
        match_count: int = 5,
        similarity_threshold: float = 0.2,
    ) -> list[KnowledgeSearchMatch]: ...
