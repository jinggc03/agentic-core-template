"""Tests for KnowledgeSearchSkill."""

from app.knowledge.base import RAGConfigurationError
from app.knowledge.chunking import TextChunker
from app.knowledge.embeddings import OpenAIEmbeddingProvider
from app.knowledge.memory import InMemoryKnowledgeRepository
from app.knowledge.service import RAGService
from app.skills.rag.knowledge_search import KnowledgeSearchSkill


class FakeEmbeddingProvider:
    model = "fake-embedding-model"
    dimensions = 2

    def embed_texts(self, texts):
        embeddings = []
        for text in texts:
            if text.lower().startswith("alpha"):
                embeddings.append([1.0, 0.0])
            elif "beta" in text.lower():
                embeddings.append([0.0, 1.0])
            else:
                embeddings.append([1.0, 0.0])
        return embeddings


def build_skill(enabled=True, embedding_provider=None):
    service = RAGService(
        repository=InMemoryKnowledgeRepository(),
        embedding_provider=embedding_provider or FakeEmbeddingProvider(),
        chunker=TextChunker(chunk_size_chars=20, overlap_chars=0),
        enabled=enabled,
    )
    return KnowledgeSearchSkill(rag_service=service)


def test_knowledge_search_skill_ingests_text():
    skill = build_skill()

    result = skill.run(
        {
            "operation": "ingest_text",
            "text": "alpha content beta content",
            "title": "Doc",
            "owner_id": "user-1",
            "metadata": {"source": "unit"},
        }
    )

    assert result["chunks_created"] == 2
    assert result["embedding_model"] == "fake-embedding-model"
    assert result["document_id"]


def test_knowledge_search_skill_queries_context():
    skill = build_skill()
    skill.run(
        {
            "operation": "ingest_text",
            "text": "alpha content beta content",
            "owner_id": "user-1",
        }
    )

    result = skill.run(
        {
            "operation": "query",
            "query": "alpha",
            "owner_id": "user-1",
            "match_count": 1,
            "similarity_threshold": 0.0,
        }
    )

    assert result["query"] == "alpha"
    assert len(result["matches"]) == 1
    assert "alpha" in result["context"]
    assert {"document_id", "chunk_id", "content", "similarity", "metadata"} <= set(
        result["matches"][0]
    )


def test_knowledge_search_skill_returns_clear_error_when_disabled():
    skill = build_skill(enabled=False)

    result = skill.run({"operation": "query", "query": "alpha"})

    assert "error" in result
    assert "RAG is disabled" in result["error"]


def test_knowledge_search_skill_returns_clear_error_when_embedding_key_missing():
    service = RAGService(
        repository=InMemoryKnowledgeRepository(),
        embedding_provider=OpenAIEmbeddingProvider(api_key=""),
        chunker=TextChunker(),
        enabled=True,
    )
    skill = KnowledgeSearchSkill(rag_service=service)

    result = skill.run({"operation": "query", "query": "alpha"})

    assert "error" in result
    assert "OPENAI_API_KEY or EMBEDDING_API_KEY" in result["error"]


def test_knowledge_search_skill_rejects_unknown_operation():
    skill = build_skill()

    result = skill.run({"operation": "delete"})

    assert result == {"error": "Unknown operation: delete"}
