"""Tests for knowledge repositories."""

from app.knowledge.base import KnowledgeChunkRecord, KnowledgeDocumentRecord
from app.knowledge.memory import InMemoryKnowledgeRepository
from app.knowledge.supabase import SupabaseKnowledgeRepository


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTableQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.payload = None

    def upsert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        table = self.client.tables.setdefault(self.table_name, [])
        if isinstance(self.payload, list):
            table.extend(self.payload)
            return FakeResponse(self.payload)
        table.append(self.payload)
        return FakeResponse([self.payload])


class FakeRpcQuery:
    def __init__(self, client, name, payload):
        self.client = client
        self.name = name
        self.payload = payload

    def execute(self):
        self.client.rpc_calls.append((self.name, self.payload))
        return FakeResponse(
            [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "content": "matched content",
                    "similarity": 0.91,
                    "metadata": {"source": "test"},
                }
            ]
        )


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {}
        self.rpc_calls = []

    def table(self, table_name):
        return FakeTableQuery(self, table_name)

    def rpc(self, name, payload):
        return FakeRpcQuery(self, name, payload)


def test_memory_knowledge_repository_searches_by_similarity_and_owner():
    repository = InMemoryKnowledgeRepository()
    repository.save_document(KnowledgeDocumentRecord(id="doc-1", owner_id="user-1"))
    repository.save_chunks(
        [
            KnowledgeChunkRecord(
                id="chunk-1",
                document_id="doc-1",
                owner_id="user-1",
                content="alpha",
                chunk_index=0,
                embedding=[1.0, 0.0],
            ),
            KnowledgeChunkRecord(
                id="chunk-2",
                document_id="doc-1",
                owner_id="user-2",
                content="beta",
                chunk_index=1,
                embedding=[1.0, 0.0],
            ),
        ]
    )

    matches = repository.search_chunks(
        query_embedding=[1.0, 0.0],
        owner_id="user-1",
        match_count=5,
        similarity_threshold=0.1,
    )

    assert len(matches) == 1
    assert matches[0].chunk_id == "chunk-1"
    assert matches[0].similarity == 1.0


def test_supabase_knowledge_repository_saves_and_searches_via_rpc():
    client = FakeSupabaseClient()
    repository = SupabaseKnowledgeRepository(client=client)

    document = repository.save_document(KnowledgeDocumentRecord(id="doc-1", owner_id="user-1"))
    chunks = repository.save_chunks(
        [
            KnowledgeChunkRecord(
                id="chunk-1",
                document_id="doc-1",
                owner_id="user-1",
                content="alpha",
                chunk_index=0,
                embedding=[1.0, 0.0],
            )
        ]
    )
    matches = repository.search_chunks(
        query_embedding=[1.0, 0.0],
        owner_id="user-1",
        match_count=3,
        similarity_threshold=0.2,
    )

    assert document.id == "doc-1"
    assert chunks[0].id == "chunk-1"
    assert matches[0].content == "matched content"
    assert client.rpc_calls == [
        (
            "match_knowledge_chunks",
            {
                "query_embedding": [1.0, 0.0],
                "match_count": 3,
                "similarity_threshold": 0.2,
                "filter_owner_id": "user-1",
            },
        )
    ]
