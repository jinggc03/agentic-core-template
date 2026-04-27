# Architecture

This document describes the architecture of `agentic-core-template`.

---

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI (Transport)                  │
│                                                          │
│  GET  /api/agents          List registered agents        │
│  POST /api/agents/run      Run an agent turn  [auth]     │
│  POST /api/agents/*/reset  Reset session      [auth]     │
│  GET  /api/mcp/tools       List MCP tools                │
│  POST /api/mcp/tools/call  Call a tool        [auth]     │
│  POST /api/telegram/webhook Telegram messages            │
│  GET  /health              Health check                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                     ADK Runtime                          │
│                                                          │
│  AgentRunner                                             │
│    └── ConfiguredAgent                                   │
│          ├── ExecutionPolicy  (limits)                   │
│          ├── PolicyEnforcer   (enforcement)              │
│          └── LoopGuard        (anti-loop)                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    LLM Providers                         │
│                                                          │
│  OpenRouterProvider                                      │
│  (OpenAI-compatible — swap with any provider)           │
└─────────────────────────────────────────────────────────┘
```

---

## Layers

### Transport layer — FastAPI

`app/main.py` → `app/api/routes/`

Responsibilities:
- HTTP request/response handling
- Authentication (`X-API-Key` via `require_api_key`)
- Input validation (Pydantic request models)
- CORS enforcement
- Routing to ADK runtime or skills

The transport layer has **no business logic**. Route handlers call agents or skills and return results.

### ADK runtime — Agent Development Kit

`app/agents/base/`

The five-step turn execution pattern runs for every agent interaction:

1. **Routing** — `PolicyEnforcer.on_turn_start()` checks if turn is allowed (within `MAX_AGENT_TURNS`)
2. **Context** — agent state is gathered and injected into the turn context
3. **Message building** — user input is formatted into the provider's message format
4. **Execution** — `asyncio.wait_for(provider.generate(...), timeout=timeout_seconds)` enforces hard timeout
5. **State update** — output stored, loop guard updated, turn counter incremented

Input guards (before step 1): input length, `LoopGuard.check_input()`  
Output guards (after step 4): output truncation, `LoopGuard.check_output()`

### Skills layer

`app/skills/`

Portable, agent-agnostic capability units. Each skill:
- Has a single sync `run(input_data: dict) -> dict` method
- Returns plain data (dict, list, string)
- Has no dependency on any agent class
- Can be used by agents, MCP routes, or tested in isolation

### MCP layer

`app/api/routes/mcp.py`

Exposes skills to external MCP-compatible clients. The MCP layer is purely transport — it calls skills directly without going through the agent turn pipeline. Protected POST routes require `X-API-Key`.

### Integrations

`app/integrations/telegram/`

The Telegram bot receives messages via webhook, checks the user ID against `TELEGRAM_ALLOWED_USER_IDS`, and forwards messages to the appropriate `ConfiguredAgent` instance.

### Configuration

`app/core/config.py` — `pydantic-settings` `Settings` class

Loaded from layered `.env` files:
1. `.env.base` — shared defaults
2. `.env.<APP_ENV>` — environment overrides (dev/pre/prod)
3. `.env.local` — local machine overrides (never committed)

### Security layer

`app/core/security.py`

- `require_api_key()` — FastAPI dependency for `X-API-Key` enforcement
- `is_telegram_user_allowed()` — Telegram ID allowlist check
- `mask_secret()` / `safe_repr_settings()` — safe logging utilities

---

## Data flow: agent turn

```
Client
  │ POST /api/agents/run {"agent_id": "invoice-agent", "input": "..."}
  │ X-API-Key: <key>
  ▼
require_api_key()         ← hmac.compare_digest(), 403 if invalid
  ▼
AgentRunRequest validation ← Pydantic, 422 if malformed
  ▼
agent_registry.get(agent_id) ← 404 if unknown
  ▼
ConfiguredAgent.run_turn(user_input)
  ├── Input length check   ← TurnResult(success=False) if > MAX_INPUT_CHARS
  ├── LoopGuard.check_input()  ← TurnResult(success=False) if loop
  ├── PolicyEnforcer.on_turn_start()
  ├── PolicyEnforcer.on_model_call()
  ├── asyncio.wait_for(provider.generate(), timeout=60s)
  │     ← TimeoutError → TurnResult(success=False, "timed out")
  ├── Output truncation    ← truncate to MAX_OUTPUT_CHARS
  └── LoopGuard.check_output()
  ▼
TurnResult(success=True, output="...")
  ▼
HTTP 200 {"success": true, "output": "..."}
```

---

## Agent registry

`app/agents/registry.py`

A dict `{agent_id: AgentClass}`. Agents are instantiated on-demand and cached per session. The registry is the single registration point for all agents.

---

## Decisions

See `docs/decisions/` for Architecture Decision Records (ADRs).

Key decisions:
- [ADR-0001](decisions/0001-adk-first-runtime.md) — ADK-first runtime, why not LangChain/CrewAI
