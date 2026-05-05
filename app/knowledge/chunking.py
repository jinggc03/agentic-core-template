"""Text chunking utilities for knowledge ingestion."""


class TextChunker:
    """Deterministic character-based chunker with overlap."""

    def __init__(self, chunk_size_chars: int = 1200, overlap_chars: int = 200):
        if chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars must be greater than 0")
        if overlap_chars < 0:
            raise ValueError("overlap_chars cannot be negative")
        if overlap_chars >= chunk_size_chars:
            raise ValueError("overlap_chars must be smaller than chunk_size_chars")

        self.chunk_size_chars = chunk_size_chars
        self.overlap_chars = overlap_chars

    def chunk_text(self, text: str) -> list[str]:
        """Split text into deterministic, non-empty chunks."""
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            end = min(start + self.chunk_size_chars, text_length)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == text_length:
                break
            start = max(end - self.overlap_chars, start + 1)

        return chunks
