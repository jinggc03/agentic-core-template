# RAG Integration Guide

The RAG layer is optional infrastructure for projects that need retrieval over project knowledge. Agents should consume RAG through `KnowledgeSearchSkill` or `RAGService`, not through Supabase or pgvector directly.

## Architecture

```text
Agent
  -> KnowledgeSearchSkill
  -> RAGService
  -> EmbeddingProvider + KnowledgeRepository
  -> Memory or Supabase pgvector
```

The first functional backend is Supabase pgvector. The contracts live under `app/knowledge/` so cloned projects can add another vector store later.

## Configuration

RAG is disabled by default:

```yaml
rag:
  enabled: false
  backend: supabase
  chunk_size_chars: 1200
  chunk_overlap_chars: 200

embeddings:
  provider: openai
  model: text-embedding-3-small
  dimensions: 1536
```

Secrets belong in `.env`:

```bash
EMBEDDING_API_KEY=
OPENAI_API_KEY=
```

`EMBEDDING_API_KEY` takes priority for embeddings. If it is empty, the OpenAI embedding provider falls back to `OPENAI_API_KEY`.

## Ingest Text

```python
from app.skills.rag import KnowledgeSearchSkill

skill = KnowledgeSearchSkill()
result = skill.run(
    {
        "operation": "ingest_text",
        "text": "Project knowledge goes here.",
        "title": "Project Notes",
        "source": "manual",
        "owner_id": "user-or-project-id",
        "metadata": {"kind": "notes"},
    }
)
```

Response:

```json
{
  "document_id": "...",
  "chunks_created": 1,
  "embedding_model": "text-embedding-3-small"
}
```

## Query

```python
result = skill.run(
    {
        "operation": "query",
        "query": "What does the project say about invoices?",
        "owner_id": "user-or-project-id",
        "match_count": 5,
        "similarity_threshold": 0.2,
    }
)
```

Response:

```json
{
  "query": "What does the project say about invoices?",
  "matches": [
    {
      "document_id": "...",
      "chunk_id": "...",
      "content": "...",
      "similarity": 0.87,
      "metadata": {}
    }
  ],
  "context": "retrieved context"
}
```

## Supabase pgvector

Supabase-backed RAG requires:

```yaml
integrations:
  supabase:
    enabled: true

rag:
  enabled: true
  backend: supabase
```

Apply migrations with:

```bash
make supabase-reset
```

The migration creates:

- `knowledge_documents`
- `knowledge_chunks`
- `knowledge_chunks_embedding_idx`
- `match_knowledge_chunks`

## Testing

Default suite:

```bash
python -m pytest -q
```

Optional real/local Supabase RAG test:

```bash
SUPABASE_TESTS=true RAG_TESTS=true RAG_ENABLED=true SUPABASE_ENABLED=true python -m pytest tests/integration/test_supabase_rag.py -q
```

## Out of Scope

- PDF parsing.
- Web crawling.
- Reranking.
- Hybrid keyword/vector search.
- Streaming retrieval.
- Multi-backend vector stores beyond the current contracts.
