# EPIC: v0.4 Supabase Integration for Agentic Core Template

## Epic Summary

Turn Supabase from a configuration placeholder into an optional, well-abstracted infrastructure layer for cloned projects.

The goal is not to couple agents directly to Supabase. The goal is to provide reusable repository interfaces, Supabase-backed implementations, migrations, RLS policies, local development commands, and docs so projects can start with persistence, storage, auth-ready boundaries, and auditability without rewriting the template architecture.

## Business Value

- Projects cloned from the template can persist conversations, messages, snapshots, files, and audit events from day one.
- Agents and skills remain portable because they depend on repository interfaces, not on the Supabase SDK.
- Supabase can provide Postgres, Storage, Auth, RLS, and local development workflows without weakening the ADK-first runtime.
- The template becomes more useful for real projects while preserving testability and clean architecture.

## Non-Goals

- Do not make Supabase mandatory for local development.
- Do not call Supabase directly from agents, skills, routes, or Telegram handlers.
- Do not implement a full product-specific data model.
- Do not add RAG or pgvector in this epic unless explicitly split into a future epic.
- Do not replace FastAPI with Supabase Edge Functions.

## Architecture Rule

```text
Agent / Skill / API route
  -> Repository interface
  -> Supabase repository implementation
  -> Supabase client / Postgres / Storage
```

Avoid:

```text
Agent / Skill / API route
  -> Supabase SDK directly
```

---

## JIRA Cards

### SUPA-001 - Create Supabase Integration Decision Record

**Type:** Story  
**Priority:** High  
**Estimate:** 0.5 day

**Description**  
Create an ADR that defines how Supabase fits into the template: optional infrastructure, repository abstraction, supported services, security boundaries, and local development strategy.

**Scope**
- Add `docs/decisions/0002-supabase-optional-infrastructure.md`.
- Document why Supabase is optional.
- Document why agents and skills must not import the Supabase SDK directly.
- Define service-role vs anon-key usage.
- Define what belongs in `.env` vs `params/`.

**Acceptance Criteria**
- ADR exists and is written in English.
- ADR states Supabase is optional and disabled by default.
- ADR defines the repository abstraction rule.
- ADR documents service-role key restrictions.
- ADR links to configuration and security standards.

---

### SUPA-002 - Add Supabase Client Factory

**Type:** Story  
**Priority:** High  
**Estimate:** 1 day

**Description**  
Add a lazy Supabase client factory that centralizes SDK initialization and keeps SDK imports out of agents, skills, and routes.

**Scope**
- Add Supabase dependency to `pyproject.toml`.
- Create `app/integrations/supabase/client.py`.
- Provide `get_supabase_anon_client()`.
- Provide `get_supabase_service_client()`.
- Raise clear configuration errors when `SUPABASE_ENABLED=true` but required settings are missing.
- Keep imports lazy so non-Supabase users can run tests without credentials.

**Acceptance Criteria**
- Supabase client code is isolated under `app/integrations/supabase/`.
- No agent, skill, or route imports the Supabase SDK directly.
- Unit tests cover disabled mode, missing config, anon client creation, and service client creation with mocks.
- Existing test suite passes without Supabase credentials.

---

### SUPA-003 - Define Repository Interfaces

**Type:** Story  
**Priority:** High  
**Estimate:** 1 day

**Description**  
Introduce repository interfaces that represent template-level persistence needs without exposing Supabase details.

**Scope**
- Create `app/repositories/base.py`.
- Define protocols or abstract base classes for:
- `ConversationRepository`
- `MessageRepository`
- `AgentStateRepository`
- `SkillRunRepository`
- `AuditLogRepository`
- `FileRepository`
- Add domain-neutral DTOs where useful.

**Acceptance Criteria**
- Repository interfaces are independent from Supabase.
- Interfaces use plain Python/Pydantic data structures.
- Agents and skills can depend on interfaces without infrastructure imports.
- Unit tests verify expected method contracts with fake implementations.

---

### SUPA-004 - Add In-Memory Repository Implementations

**Type:** Story  
**Priority:** High  
**Estimate:** 1 day

**Description**  
Provide in-memory repositories as the default implementation for tests and local development when Supabase is disabled.

**Scope**
- Create `app/repositories/memory.py`.
- Implement in-memory versions of repository interfaces.
- Add a repository provider/factory that selects memory or Supabase based on config.
- Keep current behavior unchanged when Supabase is disabled.

**Acceptance Criteria**
- Template works without Supabase credentials.
- Tests can use memory repositories.
- Repository factory defaults to memory when `SUPABASE_ENABLED=false`.
- Existing tests pass.

---

### SUPA-005 - Add Supabase Schema Migrations

**Type:** Story  
**Priority:** High  
**Estimate:** 1.5 days

**Description**  
Add versioned Supabase migrations for core template persistence tables.

**Scope**
- Add `supabase/config.toml`.
- Add `supabase/migrations/0001_core_agent_runtime.sql`.
- Add tables:
- `conversations`
- `messages`
- `agent_snapshots`
- `skill_runs`
- `audit_events`
- `files`
- Add indexes for common lookup patterns.
- Add timestamps and owner fields where needed.

**Acceptance Criteria**
- Supabase CLI can apply the migration locally.
- Tables are generic and not tied to invoice-specific business logic.
- IDs, timestamps, and metadata fields are documented.
- Migration does not store secrets.

---

### SUPA-006 - Add Baseline RLS Policies

**Type:** Story  
**Priority:** High  
**Estimate:** 1 day

**Description**  
Add safe baseline Row Level Security policies for the template tables.

**Scope**
- Enable RLS on Supabase tables.
- Add user-owned access policies for anon/authenticated use cases.
- Add backend/service-role guidance.
- Add append-only pattern for audit events where appropriate.
- Document policy assumptions.

**Acceptance Criteria**
- RLS is enabled for all user-facing tables.
- Policies are included in migrations.
- Service-role behavior is documented.
- Tests or SQL comments make policy intent clear.

---

### SUPA-007 - Implement Supabase Repository Layer

**Type:** Story  
**Priority:** High  
**Estimate:** 2 days

**Description**  
Implement Supabase-backed repositories for core runtime persistence.

**Scope**
- Create `app/repositories/supabase.py`.
- Implement conversations, messages, snapshots, skill runs, audit events, and files metadata.
- Use the client factory from `SUPA-002`.
- Map repository DTOs to Supabase rows.
- Do not expose raw SDK responses to callers.

**Acceptance Criteria**
- Supabase repositories satisfy the same interfaces as memory repositories.
- Unit tests mock client responses.
- Optional integration tests can run with `SUPABASE_TESTS=true`.
- No direct Supabase SDK usage appears outside `app/integrations/supabase/` and `app/repositories/supabase.py`.

---

### SUPA-008 - Persist Agent Turns Through Repository Interfaces

**Type:** Story  
**Priority:** High  
**Estimate:** 1.5 days

**Description**  
Wire the ADK runtime to optionally persist conversations, messages, turn results, and snapshots.

**Scope**
- Add repository injection points to `AgentRunner` or an adjacent persistence service.
- Persist user and assistant messages.
- Persist turn result metadata.
- Persist snapshots when available.
- Keep persistence failures isolated from core LLM execution unless configured otherwise.

**Acceptance Criteria**
- Existing agent behavior remains unchanged when persistence is disabled.
- Memory repository tests verify turn persistence.
- Supabase repository integration is used only through interfaces.
- Persistence errors are logged safely and do not leak secrets.

---

### SUPA-009 - Add Supabase Storage Abstraction

**Type:** Story  
**Priority:** Medium  
**Estimate:** 1.5 days

**Description**  
Add a storage abstraction for agent input files, with Supabase Storage as an optional implementation.

**Scope**
- Define file metadata model.
- Add `FileRepository` or `StorageService` interface.
- Implement Supabase Storage upload/download/signed URL support.
- Add suggested buckets:
- `agent-files`
- `invoice-documents`
- Document bucket policies.

**Acceptance Criteria**
- Agents do not call Supabase Storage directly.
- File metadata is persisted separately from raw files.
- Signed URL generation is supported by the Supabase implementation.
- Storage can be disabled without breaking the API.

---

### SUPA-010 - Add Optional Supabase Auth Dependency

**Type:** Story  
**Priority:** Medium  
**Estimate:** 1.5 days

**Description**  
Add an optional FastAPI dependency for projects that want Supabase Auth-backed multi-user APIs.

**Scope**
- Create `app/api/auth.py` or `app/integrations/supabase/auth.py`.
- Validate Supabase JWTs when auth mode is enabled.
- Extract `user_id`.
- Make ownership available to repositories.
- Keep existing `X-API-Key` flow intact.

**Acceptance Criteria**
- Supabase Auth is disabled by default.
- API key auth continues to work.
- Tests cover missing token, invalid token, and valid mocked token.
- Auth dependency does not require Supabase credentials unless enabled.

---

### SUPA-011 - Add Audit Event Logging

**Type:** Story  
**Priority:** Medium  
**Estimate:** 1 day

**Description**  
Add a template-level audit service for agent runtime events.

**Scope**
- Create `app/services/audit.py`.
- Emit events for:
- agent turn started
- agent turn completed
- model call blocked by policy
- loop detected
- timeout
- tool call started/completed
- webhook rejected
- Store events through `AuditLogRepository`.

**Acceptance Criteria**
- Audit logging uses repository interfaces.
- Audit event payloads are safe and do not include secrets.
- Tests cover at least success, failure, and blocked execution events.

---

### SUPA-012 - Add Supabase Local Development Commands

**Type:** Story  
**Priority:** Medium  
**Estimate:** 0.5 day

**Description**  
Add Makefile commands and docs for local Supabase workflows.

**Scope**
- Add Makefile commands:
- `make supabase-start`
- `make supabase-stop`
- `make supabase-reset`
- `make supabase-migrate`
- `make supabase-status`
- Document prerequisite: Supabase CLI.

**Acceptance Criteria**
- Commands are documented in `README.md`.
- Commands fail clearly if Supabase CLI is missing.
- Existing Makefile commands remain unchanged.

---

### SUPA-013 - Document Supabase Setup

**Type:** Story  
**Priority:** Medium  
**Estimate:** 1 day

**Description**  
Create complete setup docs for using Supabase with this template.

**Scope**
- Add `docs/standards/supabase-integration-guide.md`.
- Cover local development.
- Cover cloud project setup.
- Cover `.env` secrets.
- Cover `params/` settings.
- Cover RLS and service-role warnings.
- Cover repository usage patterns.

**Acceptance Criteria**
- Guide is written in English.
- Guide distinguishes local vs hosted Supabase.
- Guide explains which services are implemented and optional.
- README links to the guide.

---

### SUPA-014 - Add Optional Supabase Integration Tests

**Type:** Story  
**Priority:** Medium  
**Estimate:** 1 day

**Description**  
Add integration tests that can run against a real/local Supabase instance without making Supabase mandatory for the default suite.

**Scope**
- Add `tests/integration/test_supabase_repositories.py`.
- Gate tests behind `SUPABASE_TESTS=true`.
- Use test data cleanup.
- Test conversations, messages, snapshots, audit events, and file metadata.

**Acceptance Criteria**
- Default `python -m pytest` passes without Supabase.
- Supabase integration tests run only when explicitly enabled.
- Tests document required env vars.
- Tests clean up their own data.

---

### SUPA-015 - Update Public Template README and Audit

**Type:** Story  
**Priority:** Low  
**Estimate:** 0.5 day

**Description**  
Update public documentation and audit report to reflect the completed Supabase integration.

**Scope**
- Update `README.md`.
- Update `reports/architecture_audit.md`.
- Update project status from Supabase-ready to Supabase-integrated.
- Keep production caveats honest.

**Acceptance Criteria**
- README accurately describes implemented Supabase services.
- Audit report includes Supabase integration status.
- Docs do not claim Auth, Storage, or Realtime if they are not implemented.

---

## Suggested Implementation Order

1. `SUPA-001`
2. `SUPA-002`
3. `SUPA-003`
4. `SUPA-004`
5. `SUPA-005`
6. `SUPA-006`
7. `SUPA-007`
8. `SUPA-008`
9. `SUPA-011`
10. `SUPA-012`
11. `SUPA-013`
12. `SUPA-014`
13. `SUPA-009`
14. `SUPA-010`
15. `SUPA-015`

## Definition of Done for the Epic

- Supabase remains optional and disabled by default.
- Default test suite passes without Supabase credentials.
- Supabase-backed repositories exist for core runtime persistence.
- Core schema and RLS policies are versioned under `supabase/`.
- Agents, skills, and API routes do not import the Supabase SDK directly.
- Documentation explains setup, security model, and local development.
- Public README accurately describes the implemented Supabase services.
