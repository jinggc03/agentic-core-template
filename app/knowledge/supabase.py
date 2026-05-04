"""Supabase pgvector knowledge repository."""

from typing import Any, Optional

from app.integrations.supabase.client import get_supabase_service_client
from app.knowledge.base import (
    KnowledgeChunkRecord,
    KnowledgeDocumentRecord,
    KnowledgeSearchMatch,
)


def _record_to_row(record: KnowledgeDocumentRecord | KnowledgeChunkRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def _response_data(response: Any) -> Any:
    return getattr(response, "data", response)


def _list(response: Any) -> list[dict[str, Any]]:
    data = _response_data(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


class SupabaseKnowledgeRepository:
    """Knowledge repository backed by Supabase Postgres and pgvector."""

    def __init__(self, client: Any | None = None):
        self.client = client or get_supabase_service_client()

    def save_document(self, record: KnowledgeDocumentRecord) -> KnowledgeDocumentRecord:
        response = self.client.table("knowledge_documents").upsert(_record_to_row(record)).execute()
        rows = _list(response)
        return KnowledgeDocumentRecord.model_validate(rows[0] if rows else _record_to_row(record))

    def save_chunks(self, records: list[KnowledgeChunkRecord]) -> list[KnowledgeChunkRecord]:
        if not records:
            return []
        rows = [_record_to_row(record) for record in records]
        response = self.client.table("knowledge_chunks").upsert(rows).execute()
        data = _list(response) or rows
        return [KnowledgeChunkRecord.model_validate(row) for row in data]

    def search_chunks(
        self,
        *,
        query_embedding: list[float],
        owner_id: Optional[str] = None,
        match_count: int = 5,
        similarity_threshold: float = 0.2,
    ) -> list[KnowledgeSearchMatch]:
        response = self.client.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "similarity_threshold": similarity_threshold,
                "filter_owner_id": owner_id,
            },
        ).execute()
        return [KnowledgeSearchMatch.model_validate(row) for row in _list(response)]
