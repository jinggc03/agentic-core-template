# Architecture Audit - agentic-core-template (v0.4)

> Date: May 2026  
> Scope: post-v0.3 Supabase integration hardening and documentation update

---

## 1. Executive Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Overall quality | 4.6/5 | Solid, coherent template for real use |
| Simplicity (KISS) | 4.0/5 | Critical debt reduced; main path is clearer |
| SOLID | 4.1/5 | Repository boundaries isolate infrastructure from agent logic |
| YAGNI | 3.6/5 | Supabase is optional and disabled by default; some future-facing modes remain |
| Developer Experience | 4.6/5 | Stable contracts, local commands, and clearer onboarding |
| Scalability | 4.6/5 | Durable persistence path is available without coupling agents |

Verdict: the repository is now in **v0.4 = solid, secure, coherent template with optional Supabase infrastructure and controlled debt**. The highest-impact hardening and persistence foundation items are closed without regressions.

---

## 2. Critical Scope Status (v0.3)

| Item | Status |
|------|--------|
| Telegram webhook security | Done (signature validation integrated) |
| MCP integration test for `/api/mcp/tools/call` | Done |
| Telegram webhook e2e mock test | Done |
| Lazy import in `examples/invoice_agent/agent.py` | Done |
| Formal `BaseAgent` deprecation | Done |
| `prepare_turn()` real usage | Done |
| Dead flags | Registered as template future scope |
| Empty `app/mcp/server.py` | Done |
| `ALLOWED_HOSTS` | Done (middleware active) |
| Restricted CORS headers | Done |
| Audit report in English | Done |
| "Evolution Since v0.2" section | Done |

## 2.1 Supabase Integration Status (v0.4)

| Item | Status |
|------|--------|
| Supabase ADR | Done |
| Lazy Supabase client factory | Done |
| Repository interfaces | Done |
| In-memory repositories | Done |
| Supabase schema migrations | Done |
| Baseline RLS policies | Done |
| Supabase repository layer | Done |
| Optional agent turn persistence | Done |
| Storage abstraction | Done |
| Optional Supabase Auth dependency | Done |
| Audit service | Done |
| Local Supabase Makefile commands | Done |
| Supabase setup guide | Done |
| Optional integration tests | Done |
| README and audit update | Done |

---

## 3. Implemented Changes

1. **Telegram webhook hardening**
- `verify_telegram_signature()` is integrated into `POST /api/telegram/webhook`.
- Requests without signature/timestamp headers or with invalid signatures are rejected before payload processing.

2. **Integration coverage**
- MCP now has integration coverage for auth, input parsing, and response shape.
- Telegram webhook now has mock e2e coverage for allowlist behavior, handler execution, invalid signatures, and returned error text forwarding.

3. **Runtime and technical debt**
- `examples/invoice_agent/agent.py` no longer imports `settings` at module import time.
- `BaseAgent` emits a formal `DeprecationWarning` and remains only as a compatibility wrapper.
- New docs and examples point to `ConfiguredAgent`.
- `ConfiguredAgent.run_turn()` uses the `TurnContext` returned by `prepare_turn()`.
- `app/mcp/server.py` contains a real `MCPServer` implementation.
- UTC timestamps now use timezone-aware `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`.

4. **Platform security**
- `TrustedHostMiddleware` enforces `ALLOWED_HOSTS`.
- CORS request headers are restricted to `Content-Type` and `X-API-Key`.

5. **Template decisions**
- `ALLOW_AGENT_REGISTRATION` and `ENABLE_METRICS` are intentionally retained as documented template placeholders.
- They are not runtime-enforced yet and should not be treated as active controls.

---

## 4. Verification and Testing

- Current test suite result: **128 passed, 1 skipped**.
- No known regression failures after hardening.
- Deprecation warnings from `datetime.utcnow()` were removed.
- `BaseAgent` deprecation is now asserted in compatibility tests instead of leaking into the warning summary.

---

## 5. Security Status (v0.3)

### Closed
- Telegram webhook signature validation.
- Restricted CORS headers.
- Existing API key and Telegram allowlist checks preserved.
- Host header enforcement via `ALLOWED_HOSTS`.
- Supabase service-role access is isolated to backend factories/repositories.
- Baseline RLS policies are versioned with schema migrations.
- Audit payloads are sanitized before persistence.

### Remaining
- Define the operational contract for Telegram signature headers in deployment docs: expected headers, timestamp tolerance, and troubleshooting.

---

## 6. KISS / Maintainability

### Improved
- Critical flow inconsistencies were removed.
- `prepare_turn()` now participates in execution instead of acting as an unused helper.
- MCP no longer has an empty placeholder module.
- User-facing docs now promote `ConfiguredAgent` instead of legacy `BaseAgent`.

### Remaining
- `ConfiguredAgent.run_turn()` still carries multiple responsibilities and could be split internally.
- `BaseAgent` remains as a compatibility path until a future removal decision is made.

---

## 7. YAGNI and Current Debt

Non-blocking debt remains:
- `TurnMode.AGENTIC` and `TurnMode.STREAMING` are defined but not operationally used.
- `Snapshot` has partial lifecycle integration.
- MCP exposes transport endpoints, but still has limited business tools.
- `ALLOW_AGENT_REGISTRATION` and `ENABLE_METRICS` are registered as template placeholders, not active runtime features.

---

## 8. Current Technical Risks

| Risk | Probability | Impact | Note |
|------|-------------|--------|------|
| MCP without business tools | High | Medium | Transport is ready, functional value is still limited |
| YAGNI debt in stubs and unused modes | Medium | Medium | Can confuse onboarding if left unexplained |
| Legacy `BaseAgent` path | Medium | Medium | Controlled through deprecation and docs |
| Integration coverage remains focused | Low-Medium | Medium | Load, retry, and external failure scenarios are still future work |
| Supabase RLS assumptions may not fit every cloned product | Medium | Medium | Baseline policies must be reviewed for each product ownership model |

---

## 9. Prioritized Follow-Up

### High Priority

1. Define a removal timeline for `BaseAgent`.
2. Implement at least one production-style MCP tool with integration tests.
3. Document the operational Telegram signature contract.

### Medium Priority

4. Refactor `ConfiguredAgent.run_turn()` into smaller internal steps.
5. Decide whether `app/db/` should be removed or implemented as an MVP.
6. Decide whether `TurnMode` and `Snapshot` should be completed or trimmed.

### Low Priority

7. Expand e2e tests with external failure and retry scenarios.
8. Revisit the future-scope flags when there is a concrete metrics or dynamic registration implementation.
9. Add product-specific Supabase policies and migrations in cloned projects.
10. Add cleanup to optional integration tests if projects use long-lived shared test databases.

---

## 10. Acceptance Criteria Status

- Telegram webhook validates signature or the function is removed: **Done** (signature validation).
- Test exists for `POST /api/mcp/tools/call`: **Done**.
- Telegram webhook e2e mock test exists: **Done**.
- `invoice_agent` has no top-level `settings` import: **Done**.
- `BaseAgent` is marked as deprecated: **Done**.
- `prepare_turn()` is resolved: **Done**.
- Dead flags removed or documented: **Done** (documented future scope).
- `app/mcp/server.py` is not empty: **Done**.
- `ALLOWED_HOSTS` implemented or documented: **Done** (implemented).
- CORS headers restricted: **Done**.
- All tests pass: **Done** (128 passed, 1 skipped optional Supabase integration test).
- Report updated in English: **Done**.
- "Evolution Since v0.2" section added: **Done**.

---

## 11. Conclusion

The v0.4 Supabase work meets its objective: the template now has optional persistence, Storage/Auth helpers, audit logging, local Supabase workflows, and documentation without coupling agents to Supabase.

Recommendation: approve v0.4 for real template use and continue with controlled follow-up work.

---

## 12. Recommended v0.4 Follow-Up Plan

1. Remove or further isolate the deprecated `BaseAgent` path.
2. Add the first production-style MCP tool package.
3. Trim or complete YAGNI areas: `db` stubs, unused turn modes, and partial snapshots.
4. Decide when template placeholder flags become active runtime controls.

---

## 13. Evolution Since v0.2

### Changes Completed

- Telegram webhook signature validation was activated.
- MCP and Telegram webhook integration tests were added.
- The invoice agent lazy import issue was fixed.
- `BaseAgent` deprecation was formalized.
- User-facing examples now use `ConfiguredAgent`.
- `prepare_turn()` now has real execution usage.
- `app/mcp/server.py` now has a concrete implementation.
- `ALLOWED_HOSTS` enforcement was activated.
- CORS headers were restricted.
- Deprecated UTC timestamp calls were replaced.
- Template-only flags were documented as future scope.

### Quality Impact

- Lower abuse risk in external integrations.
- Higher confidence from integration test coverage.
- Clearer contracts for developers using the template.
- Better future compatibility through timezone-aware timestamps.
- Better template onboarding because legacy paths are no longer promoted.

### Remaining Debt

- Deprecated `BaseAgent` compatibility code still exists.
- MCP still needs business-ready tools.
- YAGNI components remain: unused modes and partial snapshots.
- Template placeholder flags remain intentionally registered but inactive.

---

## 14. Evolution Since v0.3

### Changes Completed

- Supabase integration ADR added.
- Lazy Supabase client factory added.
- Repository interfaces and in-memory implementations added.
- Supabase schema migration and baseline RLS policies added.
- Supabase-backed repositories added for core runtime persistence.
- `AgentRunner` can persist conversations, messages, turn metadata, and state through repository interfaces.
- Supabase Storage helper added for upload, download, and signed URLs.
- Optional Supabase Auth dependency added for route-level Bearer token validation.
- Audit service added with payload secret redaction.
- Local Supabase Makefile commands added.
- Optional Supabase integration tests added behind `SUPABASE_TESTS=true`.
- Public README and Supabase setup docs updated.

### Quality Impact

- Cloned projects can start with durable persistence without rewriting architecture.
- Agents, skills, routes, Telegram, and MCP remain isolated from the Supabase SDK.
- Default test and local development paths still work without Supabase credentials.
- Security posture improved through RLS baseline, service-role isolation, and audit redaction.

### Remaining Debt

- RLS policies are safe baseline defaults, not a substitute for product-specific authorization design.
- Optional integration tests require a real/local Supabase instance and are skipped by default.
- Realtime, Edge Functions, pgvector/RAG, Cron, and Queues remain intentionally out of scope.
- `BaseAgent` is still deprecated but not removed.
