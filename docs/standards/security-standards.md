# Security Standards

This document defines the security requirements for the agentic-core codebase. All contributors must follow these standards.

---

## Authentication

`AUTH_MODE` is the canonical authentication mechanism for FastAPI protected endpoints.

Supported modes:

| Mode | Use case | Runtime behavior |
|------|----------|------------------|
| `off` | Local development only | Returns an anonymous `AuthContext`; rejected when `APP_ENV=prod` |
| `api_key` | Simple backend deployments | Requires `X-API-Key` and compares with `API_KEY` using `hmac.compare_digest()` |
| `supabase_auth` | User-facing deployments using Supabase Auth | Requires `Authorization: Bearer <jwt>` and validates with `SUPABASE_JWT_SECRET` |

`API_KEY_ENABLED` remains only for backward compatibility with legacy `require_api_key` imports. New protected endpoints must use `get_auth_context`.

Protected endpoint pattern:

```python
from app.api.deps import get_auth_context
from app.auth.context import AuthContext
from fastapi import Depends

@router.post("/my-endpoint")
async def my_handler(
    request: MyRequest,
    auth_context: AuthContext = Depends(get_auth_context),
):
    ...
```

### AuthContext

`AuthContext` is the runtime identity boundary:

```python
class AuthContext:
    actor_id: str | None
    auth_mode: str
    tenant_id: str | None
    roles: list[str]
    scopes: list[str]
```

Rules:

- Agents, skills, routes, and Telegram handlers must not depend on Supabase Auth internals.
- `tenant_id`, `roles`, and `scopes` are future-ready and empty by default.
- Do not trust mutable Supabase claims such as `user_metadata` for tenant, roles, or scopes.
- Authorization policy should live outside agent reasoning.

### Supabase Auth

When `AUTH_MODE=supabase_auth`:

- Validate JWT locally with `HS256` and `SUPABASE_JWT_SECRET`.
- Require the `sub` claim and map it to `AuthContext.actor_id`.
- Let JWT expiration validation reject expired tokens.
- Return `401` for missing, invalid, or expired tokens.
- Return `503` when `SUPABASE_JWT_SECRET` is missing.

`SUPABASE_SERVICE_ROLE_KEY` is backend-only and must never be exposed to clients.

### Telegram webhook exception

`POST /api/telegram/webhook` must not use `get_auth_context`. It keeps webhook-specific security:

- Telegram signature validation
- Timestamp tolerance validation
- `TELEGRAM_ALLOWED_USER_IDS` allowlist

After signature and allowlist validation, the handler may create:

```python
AuthContext(auth_mode="telegram_webhook", actor_id=str(user_id))
```

### New endpoints checklist

When adding a new protected endpoint:

- [ ] Add `auth_context: AuthContext = Depends(get_auth_context)` to the signature
- [ ] Add tests for valid auth, missing auth, and invalid auth
- [ ] Keep public webhook exceptions explicitly documented
- [ ] Add the endpoint to the Client Integration Guide when client-facing

---

## CORS policy

### Rule: No wildcard

`CORS_ALLOWED_ORIGINS` must be an explicit list of origins. The app code strips `*` from the list even if accidentally set.

### Allowed methods

Only `GET` and `POST` are allowed in CORS. This is enforced in `app/main.py`.

### Configuration

```env
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://your-admin.com
```

In development:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Telegram allowlist

### Rule: Restrict in production

In production, `TELEGRAM_ALLOWED_USER_IDS` must be set to an explicit list of trusted user IDs. An empty list grants access to all Telegram users.

```env
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
```

### Enforcement

The webhook handler silently ignores unauthorized users by returning `{"ok": true}` with no error message. This prevents information leakage about the allowlist.

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

Use stricter values in production.

---

## Anti-loop protection

The `LoopGuard` detects:

- Identical user input repeated at least 3 consecutive turns
- Same tool called at least 5 times consecutively
- Identical output repeated at least 3 consecutive turns

When detected, `run_turn()` returns `TurnResult(success=False, error="Loop detected...")` and does not call the LLM.

---

## Safe logging

### Rules

1. Never log secret values: API keys, tokens, passwords, service role keys, JWT secrets.
2. Never log full request bodies containing user-provided data.
3. Log security events without secret values.

### Using `mask_secret()`

```python
from app.core.security import mask_secret

logger.info(f"Using API key: {mask_secret(settings.API_KEY)}")
```

### Using `safe_repr_settings()`

```python
from app.core.security import safe_repr_settings

logger.info(f"Startup config: {safe_repr_settings(settings.model_dump())}")
```

### Startup logging checklist

On startup, log:

- `APP_ENV`, `LLM_PROVIDER`, `LLM_MODEL`
- `AUTH_MODE`
- Whether Telegram is enabled and whether an allowlist is set
- Never log `API_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, or Supabase service-role keys

---

## Docs / OpenAPI in production

`/docs`, `/redoc`, and `/openapi.json` are disabled when `APP_ENV=prod`. This prevents exposing the API schema to unauthorized parties.

---

## Dependency security

- Pin dependencies with compatible ranges in `pyproject.toml`
- Run `pip audit` or `safety check` in CI when available
- Never install untrusted packages in the agent runtime environment

---

## Checklist for new features

- [ ] New protected endpoints use `Depends(get_auth_context)`
- [ ] Public webhooks have explicit webhook-specific security
- [ ] No secrets in code, logs, or committed `.env` files
- [ ] New config variables are documented in `.env.example` and configuration standards
- [ ] CORS not widened beyond current policy
- [ ] Execution limits not loosened without documented justification
- [ ] Tests cover happy path, missing auth, and invalid input
