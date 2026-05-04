"""Knowledge layer for optional RAG workflows."""

from app.knowledge.base import (
    EmbeddingProvider,
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    KnowledgeRepository,
    KnowledgeSearchMatch,
    RAGConfigurationError,
)
from app.knowledge.chunking import TextChunker
from app.knowledge.factory import get_rag_service
from app.knowledge.service import RAGService

__all__ = [
    "EmbeddingProvider",
    "KnowledgeChunkRecord",
    "KnowledgeDocumentRecord",
    "KnowledgeRepository",
    "KnowledgeSearchMatch",
    "RAGConfigurationError",
    "RAGService",
    "TextChunker",
    "get_rag_service",
]
