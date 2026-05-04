# AGENTS.md — AI Coding Agent Instructions

This file provides context and constraints for AI coding agents (Codex, Copilot, Cursor, Claude, etc.) working in this repository.

---

## What this repo is

`agentic-core-template` is a **production-ready FastAPI backend** for building AI agents using the ADK (Agent Development Kit) architecture. It provides:

- A structured five-step agent turn execution pattern
- Modular skill system (portable, reusable capability units)
- MCP (Model Context Protocol) exposure layer for external tool access
- Telegram bot integration
- Layered environment configuration with security guardrails

---

## Architecture summary

```
FastAPI (transport/API layer)
  └── /api/agents/*    → AgentRunner → ConfiguredAgent → LLM provider
  └── /api/mcp/*       → Skill execution (direct, no agent state)
  └── /api/telegram/*  → TelegramHandler → ConfiguredAgent

ADK runtime (app/agents/base/)
  ├── ConfiguredAgent  → base class for all agents
  ├── AgentRunner      → orchestrates turn execution
  ├── ExecutionPolicy  → enforces model/tool/turn limits
  └── LoopGuard        → detects runaway loops

Skills (app/skills/)
  └── Portable capability units — no agent dependency

Providers (app/providers/)
  └── LLM provider abstraction (openrouter, openai, etc.)
```

---

## ADK-first rule

**Every agent must be a `ConfiguredAgent` subclass.** Do not call LLM providers directly from routes, handlers, or skills. All LLM access goes through the ADK execution pipeline.

The five-step turn pattern is not optional — it provides input validation, rate limiting, timeout enforcement, and loop detection for every turn automatically.

`BaseAgent` is deprecated and exists only as a compatibility wrapper. New code must use `ConfiguredAgent`.

---

## Skills are portable

Skills in `app/skills/` must not import from `app/agents/`. A skill is a reusable unit that can be used by any agent, exposed via MCP, or tested in isolation.

---

## No hardcoded secrets

- Never hardcode API keys, tokens, or passwords in source code
- All secrets come from environment variables loaded via `app/core/config.py`
- Use `settings.<FIELD>` everywhere — never `os.environ.get(...)` directly

---

## Any new env var → params/ or .env.example

When you add a new `Field(...)` to `app/core/config.py`, you MUST also:
1. **Non-secret values** → add to `params/base/params.yml` (and update each env override file as needed in `params/{dev,pre,prod}/params.yml`)
2. **Secret values** (keys, tokens, passwords) → add to `.env.example` with a placeholder comment
3. Add it to the variable reference table in `docs/standards/configuration-standards.md`

---

## Any new POST endpoint → define security

Every new `POST` endpoint under `/api/` must:
1. Add `auth_context: AuthContext = Depends(get_auth_context)` unless it is explicitly a public webhook
2. Add tests for both authenticated and unauthenticated access

Public webhook exception: `/api/telegram/webhook` uses Telegram signature/timestamp validation and `TELEGRAM_ALLOWED_USER_IDS`, then creates `AuthContext(auth_mode="telegram_webhook", actor_id=str(user_id))`.

`require_api_key` exists only as a backward-compatible wrapper. New protected endpoints must use `get_auth_context`.

---

## Test requirements

- Every new agent must have at least one test in `tests/`
- Every new skill must have at least one test
- Every new security-sensitive path must have auth tests
- Run `python -m pytest` from the project root to verify

---

## Folder structure

```
app/
├── agents/
│   ├── base/           # ADK framework — do not modify for individual agents
│   └── registry.py     # Register new agents here
├── api/
│   ├── deps.py         # FastAPI dependency injection (get_auth_context, legacy require_api_key)
│   └── routes/         # One file per surface (agent, mcp, telegram, health)
├── core/
│   ├── config.py       # All settings — pydantic-settings
│   ├── logging.py      # Structured logging helpers
│   └── security.py     # API key auth, Telegram allowlist, safe logging
├── integrations/
│   └── telegram/       # Telegram bot and handler
├── providers/          # LLM provider abstraction
└── skills/             # Portable skill implementations

docs/
├── architecture.md
├── decisions/          # Architecture Decision Records
└── standards/          # Developer guides

examples/
└── invoice_agent/      # Reference ADK implementation

tests/
├── test_adk_architecture.py
└── test_security_guardrails.py
```

---

## What not to change

- `app/agents/base/` — the ADK framework is intentionally stable. Modify agents, not the base framework
- `app/core/config.py` field defaults — defaults are safe conservative values; loosening them in prod requires documentation
- CORS policy — never add `"*"` to allowed origins
- Execution limits — never increase them without documented justification in `docs/decisions/`
