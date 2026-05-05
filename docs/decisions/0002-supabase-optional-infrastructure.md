# ADR-0002: Supabase as Optional Infrastructure

**Status:** Accepted  
**Date:** 2026  
**Deciders:** Core team

---

## Context

This repository is a reusable template for building ADK-first AI agents. It should help cloned projects start with clean persistence, file storage, auditability, and user-boundary options without forcing any external platform on users who only need the base FastAPI and agent runtime.

Supabase is a good fit for many cloned projects because it provides hosted/local Postgres, Row Level Security (RLS), Storage, Auth, and local development tooling. However, using Supabase directly from agents or skills would couple portable runtime logic to one infrastructure provider and weaken the template boundaries.

---

## Decision

Supabase is treated as **optional infrastructure**, disabled by default.

Supabase access must go through integration factories and repository interfaces. Agents, skills, API routes, Telegram handlers, and MCP routes must not import the Supabase SDK directly.

The intended dependency direction is:

```text
Agent / Skill / API route
  -> Repository interface
  -> Supabase repository implementation
  -> Supabase client factory
  -> Supabase SDK
```

The following values belong in `.env` because they are secrets or private deployment values:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL`

The following values belong in versioned `params/` files because they are non-secret runtime configuration:

- `integrations.supabase.enabled`
- future non-secret Supabase feature flags

`SUPABASE_ANON_KEY` is intended for RLS-safe operations. `SUPABASE_SERVICE_ROLE_KEY` is backend-only, bypasses RLS, and must never be exposed to browsers, clients, logs, telemetry, or generated responses.

FastAPI remains the backend runtime for this template. Supabase Edge Functions are out of scope unless a future decision explicitly adds them.

---

## Rationale

- Keeps agents and skills portable across infrastructure providers.
- Preserves the ADK-first rule: agents execute through `ConfiguredAgent` and `AgentRunner`, not through infrastructure code.
- Allows default local development and the default test suite to run without Supabase credentials.
- Makes future persistence work testable with in-memory repositories and optional Supabase-backed repositories.
- Prevents accidental service-role leakage by centralizing client creation and key usage.

---

## Consequences

### Positive

- Projects can opt into Supabase without changing agent code.
- Repository interfaces can support in-memory, Supabase, or future database implementations.
- Supabase-specific security rules can be documented and tested in one layer.
- Public template users can clone and run the project without a Supabase account.

### Negative

- Adds an infrastructure abstraction layer that must be maintained.
- Supabase features are not available until repository implementations and migrations are added.
- Some integration tests must be optional because they require a real or local Supabase instance.

---

## Implementation Rules

1. Supabase SDK imports are allowed only under `app/integrations/supabase/` and Supabase-specific repository implementations.
2. Agents, skills, API routes, MCP routes, and Telegram handlers must depend on repository interfaces or services, not on Supabase clients.
3. Client factories must initialize lazily so disabled Supabase configuration does not break startup or tests.
4. Service-role clients are backend-only and must be clearly named as such.
5. Errors caused by missing Supabase configuration should fail clearly when Supabase is used, not during default application import.

---

## References

- [Configuration guide](../configuration.md)
- [Configuration standards](../standards/configuration-standards.md)
- [Security standards](../standards/security-standards.md)
