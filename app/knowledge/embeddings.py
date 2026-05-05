"""Embedding provider implementations."""

import json
from typing import Any
from urllib import error, request

from app.knowledge.base import RAGConfigurationError


class OpenAIEmbeddingProvider:
    """OpenAI embeddings provider using the official embeddings API."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.model = model
        self.dimensions = dimensions
        self.base_url = "https://api.openai.com/v1"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts."""
        if not self.api_key:
            raise RAGConfigurationError(
                "OPENAI_API_KEY or EMBEDDING_API_KEY must be configured when RAG is enabled."
            )
        if not texts:
            return []

        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }
        if self.dimensions:
            payload["dimensions"] = self.dimensions

        data = self._post_embeddings(payload)
        embeddings = [item["embedding"] for item in data.get("data", [])]
        if len(embeddings) != len(texts):
            raise RAGConfigurationError("Embedding provider returned an unexpected response shape.")
        return embeddings

    def _post_embeddings(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RAGConfigurationError(f"OpenAI embeddings API error: {exc.code}") from exc
        except error.URLError as exc:
            raise RAGConfigurationError(f"OpenAI embeddings API request failed: {exc}") from exc
