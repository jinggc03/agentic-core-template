# Project Context

> For AI coding agents working in this repository (Codex, etc.)

---

## Purpose

Production-ready FastAPI backend template for building AI agents using the ADK (Agent Development Kit) architecture. Provides:

- Structured agent execution with safety guardrails
- Modular skills that are portable and testable in isolation
- MCP exposure layer for external tool access
- Telegram bot integration
- Layered environment configuration

---

## Folder map

```
app/
├── agents/
│   ├── base/
│   │   ├── configured_agent.py   # Base agent class — 5-step turn pattern
│   │   ├── execution_policy.py   # Rate limits, tool scope, turn limits
│   │   ├── loop_guard.py         # Anti-loop detection
│   │   ├── types.py              # TurnResult, TurnContext, TurnMode, etc.
│   │   └── __init__.py
│   └── registry.py               # {agent_id: AgentClass} mapping
├── api/
│   ├── deps.py                   # get_auth_context dependency and legacy require_api_key wrapper
│   └── routes/
│       ├── agent.py              # POST /run, POST /{agent_id}/run, GET /
│       ├── mcp.py                # GET /tools, POST /tools/call
│       ├── telegram.py           # POST /webhook, GET /status
│       └── health.py             # GET /health (public)
├── core/
│   ├── config.py                 # pydantic-settings Settings class
│   ├── logging.py                # get_logger(), structured log helpers
│   └── security.py               # Telegram security, legacy API key wrapper, safe logging
├── integrations/
│   └── telegram/
│       ├── bot.py                # TelegramBot wrapper
│       └── handlers.py           # TelegramHandler (routes to agents)
├── providers/                    # LLM provider abstraction
│   └── openrouter.py             # OpenRouter provider implementation
├── skills/                       # Portable skill implementations
└── main.py                       # create_app() FastAPI factory

examples/
└── invoice_agent/                # Reference ADK agent implementation
    ├── agent.py                  # InvoiceAgent(ConfiguredAgent)
    └── context.py                # InvoiceContext state

tests/
├── test_adk_architecture.py      # 22 tests — ADK framework
└── test_security_guardrails.py   # 23 tests — security & limits

docs/
├── architecture.md
├── decisions/                    # ADRs
└── standards/                    # Developer guides
```

---

## How to add a new agent

1. Create `app/agents/<my_agent>/agent.py` with a `ConfiguredAgent` subclass
2. Add `"my-agent": MyAgent` to `AGENT_REGISTRY` in `app/agents/registry.py`
3. Add at least one test in `tests/`

```python
from app.agents.base import ConfiguredAgent

class MyAgent(ConfiguredAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="You are a helpful assistant that...",
        )
```

---

## How to add a new skill

1. Create `app/skills/<my_skill>/skill.py`
2. Implement `def run(self, input_data: dict) -> dict` returning plain data
3. Do not import from `app/agents/`
4. Add a test in `tests/`

---

## How to add a new MCP tool

1. Implement the skill (see above)
2. Register it in `app/mcp/tools.py` (create if not present)
3. Wire the call in `app/api/routes/mcp.py`
4. Add `auth_context: AuthContext = Depends(get_auth_context)` to the protected handler

---

## Test commands

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_security_guardrails.py -v

# Run with coverage
python -m pytest --cov=app

# Run the server in development
APP_ENV=dev uvicorn app.main:app --reload
```

---

## Environment setup

```bash
cp .env.base.example .env.base
cp .env.dev.example .env.dev
# Create .env.local with your actual secrets (never committed)
echo "OPENROUTER_API_KEY=sk-..." > .env.local
```

---

## Key constraints for AI agents

- All agents must be `ConfiguredAgent` subclasses
- All LLM access goes through the ADK turn pipeline — never call providers directly
- Never use `*` in CORS origins
- Never print or log secret values — use `mask_secret()` from `app.core.security`
- Every new protected endpoint under `/api/` needs `Depends(get_auth_context)`
- `/api/telegram/webhook` is the explicit public webhook exception and must keep signature plus allowlist security
- Every new config variable needs to appear in all four `.env.*.example` files
- Skills must not depend on specific agents

---

## What not to modify

- `app/agents/base/` — stable ADK framework
- `app/core/config.py` default values — conservative by design
- CORS policy in `app/main.py`
- Auth logic in `app/core/security.py` — extend, don't bypass
