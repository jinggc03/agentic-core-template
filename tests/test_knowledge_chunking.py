"""Tests for deterministic RAG text chunking."""

import pytest

from app.knowledge.chunking import TextChunker


def test_text_chunker_returns_deterministic_overlapping_chunks():
    chunker = TextChunker(chunk_size_chars=10, overlap_chars=3)

    chunks = chunker.chunk_text("abcdefghij klmnopqrst")

    assert chunks == ["abcdefghij", "hij klmnop", "nopqrst"]


def test_text_chunker_normalizes_empty_text():
    chunker = TextChunker()

    assert chunker.chunk_text(" \n\t ") == []


def test_text_chunker_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="overlap_chars must be smaller"):
        TextChunker(chunk_size_chars=100, overlap_chars=100)
