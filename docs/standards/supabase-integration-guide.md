# Supabase Integration Guide

Supabase is optional infrastructure for this template. The default clone-and-run path uses in-memory repositories and does not require a Supabase project, credentials, Docker, or the Supabase CLI.

Use Supabase when a cloned project needs durable persistence, Storage, Auth-backed user context, or audit trails while keeping agents and skills portable.

## Implemented Services

- Supabase Postgres schema for conversations, messages, agent snapshots, skill runs, audit events, file metadata, and optional RAG knowledge tables.
- Baseline RLS policies for authenticated user-owned access.
- Lazy anon and service-role client factories.
- Supabase-backed repository implementations under `app/repositories/supabase.py`.
- In-memory repositories for default local development and unit tests.
- Optional Supabase Storage helper for upload, download, and signed URLs.
- Optional FastAPI dependency for validating Supabase Auth Bearer tokens.
- Optional pgvector schema, index, and `match_knowledge_chunks` RPC for RAG.
- Optional integration tests gated behind `SUPABASE_TESTS=true`.

## Not Implemented

- Realtime subscriptions.
- Edge Functions.
- Product-specific data models.
- Supabase Cron or Queues.
- Frontend Supabase clients.

## Architecture Rule

Application code should depend on repository interfaces and integration services:

```text
Agent / Skill / API route
  -> Repository interface or storage/auth service
  -> Supabase implementation
  -> Supabase SDK
```

Do not import the Supabase SDK directly from agents, skills, routes, Telegram handlers, or MCP handlers.

## Configuration

Secrets belong in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://...
```

Non-secret runtime flags belong in `params/`:

```yaml
integrations:
  supabase:
    enabled: false

rag:
  enabled: false
  backend: supabase
```

`SUPABASE_ENABLED=false` keeps the default repository factory on in-memory repositories. Set it to `true` only when the project has valid Supabase credentials and migrations applied.

## Local Supabase

Prerequisite: install the Supabase CLI.

Useful commands:

```bash
make supabase-start
make supabase-status
make supabase-reset
make supabase-stop
```

`make supabase-reset` applies migrations from `supabase/migrations/` to the local database.

## Hosted Supabase

For a hosted project:

1. Create or select a Supabase project.
2. Copy `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` into `.env`.
3. Keep `SUPABASE_SERVICE_ROLE_KEY` backend-only. Never expose it to browsers, mobile apps, logs, or client config.
4. Link the project with the Supabase CLI when you are ready to apply migrations.
5. Run `make supabase-migrate` to push migrations to the linked project.
6. Set `integrations.supabase.enabled: true` for the environment that should use Supabase repositories.

## RLS Model

All template tables in `public` have RLS enabled.

Baseline policies assume:

- Authenticated users can read/write rows they own.
- Ownership is represented by `user_id` on conversations and `owner_id` on files and knowledge records.
- Messages, snapshots, skill runs, and audit events are scoped through conversation ownership where applicable.
- Backend service-role operations bypass RLS and are used by the FastAPI runtime for repository writes.

The service-role client must be used only on the backend. If a project exposes these tables directly through the Supabase Data API, review policies for its actual product ownership model before production.

## Repository Usage

Default local usage:

```python
from app.repositories import get_repository_bundle

repositories = get_repository_bundle()
```

With `SUPABASE_ENABLED=false`, this returns in-memory repositories. With `SUPABASE_ENABLED=true`, it returns Supabase-backed repositories.

Agent turn persistence is opt-in:

```python
from app.agents.base import AgentRunner
from app.repositories import get_repository_bundle

runner = AgentRunner(
    agent,
    repositories=get_repository_bundle(),
)
```

Persistence failures are logged and do not break the core LLM turn.

## Storage Usage

Use `SupabaseStorageService` instead of calling Supabase Storage directly:

```python
from app.integrations.supabase import SupabaseStorageService

storage = SupabaseStorageService()
signed_url = storage.create_signed_url(
    bucket="agent-files",
    path="conversation/input.pdf",
)
```

Suggested buckets:

- `agent-files`
- `invoice-documents`

Persist file metadata through `FileRepository`; store raw bytes in Storage.

## RAG / pgvector Usage

The optional RAG layer uses `knowledge_documents` and `knowledge_chunks` with `vector(1536)` embeddings. The migration also defines `match_knowledge_chunks`, an RPC used by the Supabase knowledge repository.

Apply migrations locally:

```bash
make supabase-reset
```

Enable Supabase-backed RAG:

```yaml
integrations:
  supabase:
    enabled: true

rag:
  enabled: true
  backend: supabase
```

Keep `SUPABASE_SERVICE_ROLE_KEY` backend-only. User-facing products should review RLS ownership before exposing knowledge tables through the Supabase Data API.

## Auth Usage

Supabase Auth is optional. Existing `X-API-Key` backend auth remains unchanged.

Routes that want Supabase user context can opt in:

```python
from fastapi import Depends
from app.integrations.supabase.auth import SupabaseUser, get_current_supabase_user


def route(user: SupabaseUser = Depends(get_current_supabase_user)):
    return {"user_id": user.id}
```

This dependency validates a Bearer token through Supabase Auth only when used.

## Testing

Default suite:

```bash
python -m pytest
```

Optional real/local Supabase integration tests:

```bash
SUPABASE_TESTS=true SUPABASE_ENABLED=true python -m pytest tests/integration -q
SUPABASE_TESTS=true RAG_TESTS=true RAG_ENABLED=true SUPABASE_ENABLED=true python -m pytest tests/integration/test_supabase_rag.py -q
```

These tests require a configured Supabase project or local stack with migrations applied.
