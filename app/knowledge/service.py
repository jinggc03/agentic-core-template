"""RAG service orchestration."""

from typing import Any, Optional
from uuid import uuid4

from app.knowledge.base import (
    EmbeddingProvider,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    KnowledgeRepository,
    KnowledgeSearchMatch,
    RAGConfigurationError,
)
from app.knowledge.chunking import TextChunker


class RAGService:
    """Coordinate text ingestion and semantic retrieval."""

    def __init__(
        self,
        *,
        repository: KnowledgeRepository,
        embedding_provider: Optional[EmbeddingProvider],
        chunker: TextChunker,
        enabled: bool,
    ):
        self.repository = repository
        self.embedding_provider = embedding_provider
        self.chunker = chunker
        self.enabled = enabled

    @property
    def embedding_model(self) -> str:
        return self.embedding_provider.model if self.embedding_provider else ""

    def ingest_text(
        self,
        *,
        text: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        owner_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        document_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._ensure_enabled()
        if not text or not text.strip():
            raise ValueError("text is required for RAG ingestion")
        if self.embedding_provider is None:
            raise RAGConfigurationError("Embedding provider is not configured.")

        chunks = self.chunker.chunk_text(text)
        embeddings = self.embedding_provider.embed_texts(chunks)
        resolved_document_id = document_id or str(uuid4())

        document = KnowledgeDocumentRecord(
            id=resolved_document_id,
            owner_id=owner_id,
            title=title,
            source=source,
            metadata=metadata or {},
        )
        self.repository.save_document(document)
        chunk_records = [
            KnowledgeChunkRecord(
                id=str(uuid4()),
                document_id=resolved_document_id,
                owner_id=owner_id,
                content=chunk,
                chunk_index=index,
                embedding=embedding,
                metadata=metadata or {},
            )
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        self.repository.save_chunks(chunk_records)

        return {
            "document_id": resolved_document_id,
            "chunks_created": len(chunk_records),
            "embedding_model": self.embedding_model,
        }

    def query(
        self,
        *,
        query: str,
        owner_id: Optional[str] = None,
        match_count: int = 5,
        similarity_threshold: float = 0.2,
    ) -> dict[str, Any]:
        self._ensure_enabled()
        if not query or not query.strip():
            raise ValueError("query is required for RAG search")
        if self.embedding_provider is None:
            raise RAGConfigurationError("Embedding provider is not configured.")

        query_embedding = self.embedding_provider.embed_texts([query])[0]
        matches = self.repository.search_chunks(
            query_embedding=query_embedding,
            owner_id=owner_id,
            match_count=match_count,
            similarity_threshold=similarity_threshold,
        )
        return {
            "query": query,
            "matches": [_match_to_dict(match) for match in matches],
            "context": "\n\n---\n\n".join(match.content for match in matches),
        }

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise RAGConfigurationError(
                "RAG is disabled. Set RAG_ENABLED=true before using KnowledgeSearchSkill."
            )


def _match_to_dict(match: KnowledgeSearchMatch) -> dict[str, Any]:
    return match.model_dump(mode="json")
