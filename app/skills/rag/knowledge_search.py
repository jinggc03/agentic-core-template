"""Knowledge search skill for RAG workflows."""

from typing import Any, Dict, Optional

from app.knowledge.base import RAGConfigurationError
from app.knowledge.factory import get_rag_service
from app.knowledge.service import RAGService
from app.skills.base.skill import BaseSkill


class KnowledgeSearchSkill(BaseSkill):
    """Skill for text ingestion and semantic search over the knowledge layer."""

    def __init__(self, rag_service: Optional[RAGService] = None):
        super().__init__(
            name="knowledge_search",
            description="Ingests text and queries semantic context for RAG workflows",
            version="0.1.0",
        )
        self.rag_service = rag_service

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a RAG operation."""
        try:
            operation = str(input_data.get("operation", "")).lower()
            service = self.rag_service or get_rag_service()

            if operation == "ingest_text":
                return service.ingest_text(
                    text=str(input_data.get("text", "")),
                    title=input_data.get("title"),
                    source=input_data.get("source"),
                    owner_id=input_data.get("owner_id"),
                    metadata=input_data.get("metadata") or {},
                    document_id=input_data.get("document_id"),
                )
            if operation == "query":
                return service.query(
                    query=str(input_data.get("query", "")),
                    owner_id=input_data.get("owner_id"),
                    match_count=int(input_data.get("match_count", 5)),
                    similarity_threshold=float(input_data.get("similarity_threshold", 0.2)),
                )
            return {"error": f"Unknown operation: {operation}"}
        except (RAGConfigurationError, ValueError) as exc:
            return {"error": str(exc)}
