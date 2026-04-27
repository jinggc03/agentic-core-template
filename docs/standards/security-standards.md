# Security Standards

This document defines the security requirements for the agentic-core codebase. All contributors must follow these standards.

---

## API key authentication

### Enforcement

All `POST` endpoints under `/api/agents/*` and `/api/mcp/*` require the `X-API-Key` header. GET endpoints are intentionally public (discovery only).

Protected endpoint pattern:

```python
from app.api.deps import require_api_key
from fastapi import Depends

@router.post("/my-endpoint")
async def my_handler(request: MyRequest, _: str = Depends(require_api_key)):
    ...
```

### Configuration

| Variable | Requirement |
|----------|------------|
| `API_KEY_ENABLED=true` | Mandatory in production |
| `API_KEY=<value>` | Must be set when `API_KEY_ENABLED=true`; app returns 503 if missing |

### Key comparison

The key is always compared using `hmac.compare_digest()` to prevent timing attacks. Never use `==` for secret comparison.

### New endpoints checklist

When adding a new POST endpoint:
- [ ] Add `_: str = Depends(require_api_key)` to the signature
- [ ] Add an HTTP test with and without the key
- [ ] Add the endpoint to the Client Integration Guide

---

## CORS policy

### Rule: No wildcard

`CORS_ALLOWED_ORIGINS` must be an explicit list of origins. The app code strips `*` from the list even if accidentally set.

### Allowed methods

Only `GET` and `POST` are allowed in CORS. This is enforced in `app/main.py`.

### Configuration

```
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://your-admin.com
```

In development:

```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Telegram allowlist

### Rule: Restrict in production

In production, `TELEGRAM_ALLOWED_USER_IDS` must be set to an explicit list of trusted user IDs. An empty list grants access to all Telegram users.

```
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
```

### Enforcement

The webhook handler silently ignores unauthorized users (returns `{"ok": true}` with no error message). This prevents information leakage about the allowlist.

---

## Execution limits

All agent executions are bounded by hard limits to prevent abuse:

| Limit | Default | Risk if not enforced |
|-------|---------|---------------------|
| `MAX_INPUT_CHARS` | 8000 | Prompt injection via large inputs |
| `MAX_OUTPUT_CHARS` | 12000 | Output flooding / memory exhaustion |
| `MAX_MODEL_CALLS_PER_TURN` | 1 | Runaway LLM usage |
| `MAX_TOOL_CALLS_PER_TURN` | 5 | Tool abuse loops |
| `MAX_AGENT_TURNS` | 10 | Infinite conversation sessions |
| `AGENT_TIMEOUT_SECONDS` | 60 | Hanging connections / resource exhaustion |

Use stricter values in production (see `.env.prod.example`).

---

## Anti-loop protection

The `LoopGuard` (per `ConfiguredAgent` instance) detects:

- Identical user input repeated ≥ 3 consecutive turns → `LoopDetectedError`
- Same tool called ≥ 5 times consecutively → `LoopDetectedError`
- Identical output repeated ≥ 3 consecutive turns → `LoopDetectedError`

When detected, `run_turn()` returns `TurnResult(success=False, error="Loop detected...")` and does **not** call the LLM. This prevents runaway billing and resource consumption.

---

## Safe logging

### Rules

1. **Never log secret values** — API keys, tokens, passwords, service role keys
2. **Never log full request bodies** containing user-provided data (may include PII)
3. **Log security events** — rejected API keys (without the key value), rejected Telegram users, loop detections, timeouts

### Using `mask_secret()`

```python
from app.core.security import mask_secret

logger.info(f"Using API key: {mask_secret(settings.API_KEY)}")
# → "Using API key: sk-a...xyz"
```

### Using `safe_repr_settings()`

```python
from app.core.security import safe_repr_settings

logger.info(f"Startup config: {safe_repr_settings(settings.model_dump())}")
# → All *_KEY, *_TOKEN fields replaced with "***"
```

### Startup logging checklist

On startup, log:
- ✅ `APP_ENV`, `LLM_PROVIDER`, `LLM_MODEL`
- ✅ `API_KEY_ENABLED` (bool only, not the key)
- ✅ Whether Telegram is enabled and if allowlist is set (bool only, not the IDs)
- ❌ Never log `API_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`

---

## Docs / OpenAPI in production

`/docs`, `/redoc`, and `/openapi.json` are disabled when `APP_ENV=prod`. This prevents exposing the API schema to unauthorized parties.

---

## Dependency security

- Pin all dependencies in `requirements*.txt`
- Run `pip audit` or `safety check` in CI
- Never install untrusted packages in the agent runtime environment

---

## Checklist for new features

Before merging any new feature:

- [ ] New POST endpoints have `Depends(require_api_key)`
- [ ] No secrets in code, logs, or committed `.env` files
- [ ] New config variables in all `.env.*.example` files
- [ ] CORS not widened beyond current policy
- [ ] Execution limits not loosened without documented justification
- [ ] Tests cover the happy path, missing auth, and invalid input
