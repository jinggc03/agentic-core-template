"""In-memory knowledge repository for tests and local development."""

import math
from typing import Optional

from app.knowledge.base import (
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    KnowledgeSearchMatch,
)


class InMemoryKnowledgeRepository:
    """In-memory vector repository."""

    def __init__(self):
        self.documents: dict[str, KnowledgeDocumentRecord] = {}
        self.chunks: dict[str, KnowledgeChunkRecord] = {}

    def save_document(self, record: KnowledgeDocumentRecord) -> KnowledgeDocumentRecord:
        self.documents[record.id] = record
        return record

    def save_chunks(self, records: list[KnowledgeChunkRecord]) -> list[KnowledgeChunkRecord]:
        for record in records:
            self.chunks[record.id] = record
        return records

    def search_chunks(
        self,
        *,
        query_embedding: list[float],
        owner_id: Optional[str] = None,
        match_count: int = 5,
        similarity_threshold: float = 0.2,
    ) -> list[KnowledgeSearchMatch]:
        matches: list[KnowledgeSearchMatch] = []
        for chunk in self.chunks.values():
            if owner_id is not None and chunk.owner_id != owner_id:
                continue
            similarity = _cosine_similarity(query_embedding, chunk.embedding)
            if similarity < similarity_threshold:
                continue
            matches.append(
                KnowledgeSearchMatch(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    content=chunk.content,
                    similarity=similarity,
                    metadata=chunk.metadata,
                )
            )

        matches.sort(key=lambda match: match.similarity, reverse=True)
        return matches[:match_count]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
