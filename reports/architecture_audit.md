# Architecture Audit - agentic-core-template (v0.3)

> Date: April 2026  
> Scope: post-v0.2 technical hardening (security, integration tests, minimal YAGNI cleanup)

---

## 1. Executive Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Overall quality | 4.4/5 | Solid, coherent template for real use |
| Simplicity (KISS) | 4.0/5 | Critical debt reduced; main path is clearer |
| SOLID | 3.7/5 | Good abstractions, with some SRP follow-up remaining |
| YAGNI | 3.3/5 | Minimal debt cleanup completed; non-blocking stubs remain |
| Developer Experience | 4.4/5 | Stable contracts and clearer onboarding |
| Scalability | 4.4/5 | Layered foundation is ready to evolve |

Verdict: the repository is now in **v0.3 = solid, secure, coherent template with controlled debt**. The highest-impact hardening items are closed without regressions.

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

- Current test suite result: **95 passed**.
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
- `app/db/` is still a stub.
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
- All tests pass: **Done** (95 passed).
- Report updated in English: **Done**.
- "Evolution Since v0.2" section added: **Done**.

---

## 11. Conclusion

The v0.3 hardening work meets its objective: the template is more secure, better tested, and clearer for future users. The next version should focus on MCP functional value, planned `BaseAgent` removal, and reducing remaining YAGNI debt.

Recommendation: approve v0.3 for real template use and continue with controlled follow-up work.

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
- YAGNI components remain: `db` stubs, unused modes, partial snapshots.
- Template placeholder flags remain intentionally registered but inactive.
