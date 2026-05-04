"""Knowledge layer factory."""

from typing import Any

from app.knowledge.chunking import TextChunker
from app.knowledge.embeddings import OpenAIEmbeddingProvider
from app.knowledge.memory import InMemoryKnowledgeRepository
from app.knowledge.service import RAGService


def _get_settings() -> Any:
    from app.core.config import settings

    return settings


def get_rag_service(settings: Any | None = None) -> RAGService:
    """Build the configured RAG service lazily."""
    resolved_settings = settings or _get_settings()
    chunker = TextChunker(
        chunk_size_chars=resolved_settings.RAG_CHUNK_SIZE_CHARS,
        overlap_chars=resolved_settings.RAG_CHUNK_OVERLAP_CHARS,
    )

    if not resolved_settings.RAG_ENABLED:
        return RAGService(
            repository=InMemoryKnowledgeRepository(),
            embedding_provider=None,
            chunker=chunker,
            enabled=False,
        )

    repository = _build_repository(resolved_settings)
    embedding_provider = OpenAIEmbeddingProvider(
        api_key=resolved_settings.EMBEDDING_API_KEY or resolved_settings.OPENAI_API_KEY,
        model=resolved_settings.EMBEDDING_MODEL,
        dimensions=resolved_settings.EMBEDDING_DIMENSIONS,
    )
    return RAGService(
        repository=repository,
        embedding_provider=embedding_provider,
        chunker=chunker,
        enabled=True,
    )


def _build_repository(settings: Any):
    if settings.RAG_BACKEND == "supabase" and settings.SUPABASE_ENABLED:
        from app.knowledge.supabase import SupabaseKnowledgeRepository

        return SupabaseKnowledgeRepository()
    return InMemoryKnowledgeRepository()
