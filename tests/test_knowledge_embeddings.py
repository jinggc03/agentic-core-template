"""Tests for embedding providers."""

import pytest

from app.knowledge.base import RAGConfigurationError
from app.knowledge.embeddings import OpenAIEmbeddingProvider


def test_openai_embedding_provider_posts_expected_payload(monkeypatch):
    provider = OpenAIEmbeddingProvider(
        api_key="embedding-key",
        model="text-embedding-3-small",
        dimensions=1536,
    )
    captured = {}

    def fake_post(payload):
        captured.update(payload)
        return {
            "data": [
                {"embedding": [1.0, 0.0]},
                {"embedding": [0.0, 1.0]},
            ]
        }

    monkeypatch.setattr(provider, "_post_embeddings", fake_post)

    embeddings = provider.embed_texts(["alpha", "beta"])

    assert embeddings == [[1.0, 0.0], [0.0, 1.0]]
    assert captured == {
        "model": "text-embedding-3-small",
        "input": ["alpha", "beta"],
        "dimensions": 1536,
    }


def test_openai_embedding_provider_requires_api_key():
    provider = OpenAIEmbeddingProvider(api_key="")

    with pytest.raises(RAGConfigurationError, match="OPENAI_API_KEY or EMBEDDING_API_KEY"):
        provider.embed_texts(["alpha"])


def test_openai_embedding_provider_validates_response_shape(monkeypatch):
    provider = OpenAIEmbeddingProvider(api_key="embedding-key")
    monkeypatch.setattr(provider, "_post_embeddings", lambda _payload: {"data": []})

    with pytest.raises(RAGConfigurationError, match="unexpected response shape"):
        provider.embed_texts(["alpha"])
