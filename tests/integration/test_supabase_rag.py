"""Optional integration tests for real/local Supabase RAG."""

import os

import pytest

from app.knowledge.factory import get_rag_service

pytestmark = pytest.mark.skipif(
    os.getenv("SUPABASE_TESTS") != "true" or os.getenv("RAG_TESTS") != "true",
    reason="Supabase RAG integration tests are opt-in. Set SUPABASE_TESTS=true and RAG_TESTS=true.",
)


def test_supabase_rag_ingest_and_query_against_real_project():
    service = get_rag_service()
    result = service.ingest_text(
        text="RAG integration test document about invoice approvals.",
        title="RAG integration test",
        owner_id="integration-test",
    )

    query_result = service.query(
        query="invoice approvals",
        owner_id="integration-test",
        match_count=3,
        similarity_threshold=0.0,
    )

    assert result["chunks_created"] >= 1
    assert query_result["matches"]
