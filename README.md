# Agentic Core Template

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![ADK-first](https://img.shields.io/badge/ADK-first-6f42c1)
![Supabase Optional](https://img.shields.io/badge/Supabase-optional-3ecf8e)
![MIT License](https://img.shields.io/badge/license-MIT-green)
![v0.4](https://img.shields.io/badge/status-v0.4-orange)

A reusable technical foundation for building structured, secure, and extensible AI agents with ADK-first architecture.

`agentic-core-template` is a backend template for creating AI agents with good practices from the start: clear runtime boundaries, portable skills, provider abstraction, MCP exposure, FastAPI endpoints, Telegram integration, environment-based configuration, and security guardrails.

Author: Jing

## Why This Exists

AI agent projects often become hard to maintain when the runtime, prompts, tools, provider calls, API routes, and secrets all grow in the same layer. This template exists to avoid that early drift.

It addresses common problems:

- Unstructured agent implementations
- Mixed transport, orchestration, and business logic
- Secrets stored in source code or committed config
- Missing execution limits and timeout guards
- Skills that cannot be reused outside one agent
- Direct LLM calls from routes or handlers
- Hard-to-test integrations such as MCP and Telegram

## What It Provides

- ADK-first runtime built around `ConfiguredAgent` and `AgentRunner`
- FastAPI API layer for health checks, agent execution, MCP, and Telegram
- Portable skill system based on `BaseSkill.run(input_data: dict) -> dict`
- MCP-ready layer for exposing tools and resources
- Telegram bot/webhook integration with allowlist and signature checks
- LLM provider abstraction with OpenRouter, OpenAI, and DeepSeek support
- Optional Supabase infrastructure for Postgres persistence, RLS, Storage helpers, Auth helpers, and audit events
- Layered configuration with `.env` secrets and versioned `params/` YAML
- Security guardrails for API keys, CORS, host validation, safe logging, and limits
- Integration tests, architecture docs, standards, and audit reports

## Architecture

```text
Client
  -> FastAPI / Telegram / MCP
  -> AgentRunner
  -> ConfiguredAgent
  -> Skills / LLM Providers
```

Main boundaries:

- `app/api/` handles HTTP transport and request validation.
- `app/agents/base/` contains the ADK-first runtime.
- `app/agents/registry.py` registers and instantiates agents.
- `app/skills/` contains portable, reusable capabilities.
- `app/mcp/` exposes tools/resources through an MCP-style layer.
- `app/providers/` isolates LLM provider implementations.
- `app/repositories/` provides infrastructure-neutral persistence interfaces with memory and Supabase implementations.
- `app/core/` centralizes configuration, logging, and security.

## Quickstart

```bash
make install-dev
cp .env.example .env
make config-check
make run-api
```

The API runs at `http://localhost:8000`.

Useful checks:

```bash
curl http://localhost:8000/api/health/health
make test
```

Current smoke-tested behavior:

- FastAPI app loads.
- `GET /api/health/health` returns healthy status.
- A minimal `ConfiguredAgent` with a dummy provider can execute a turn.

## Creating an Agent

Every new agent should subclass `ConfiguredAgent`. Do not call LLM providers directly from API routes, Telegram handlers, or skills.

Recommended structure:

```text
app/agents/<agent_name>/
  __init__.py
  agent.py
  routing.py
  context.py
  message_builders.py
  prompt.md
```

Minimal example:

```python
from app.agents.base import ConfiguredAgent


class MyAgent(ConfiguredAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="You are a helpful assistant.",
        )
```

Register agents in `app/agents/registry.py`, then invoke them through:

- `GET /api/agents`
- `POST /api/agents/run`
- `POST /api/agents/{agent_id}/run`

For detailed guidance, see [docs/standards/agent-development-guide.md](docs/standards/agent-development-guide.md).

## Creating a Skill

Skills are portable capability units. They must not depend on `app/agents/`, so they can be reused by agents, exposed through MCP, or tested in isolation.

Contract:

```python
from typing import Any, Dict

from app.skills.base.skill import BaseSkill


class MySkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="my-skill",
            description="Does one focused task.",
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "output"}
```

For detailed guidance, see [docs/standards/skill-development-guide.md](docs/standards/skill-development-guide.md).

## Configuration

Configuration is split by sensitivity:

- `.env` stores secrets and private values only.
- `params/base/params.yml` stores shared non-secret defaults.
- `params/{dev,pre,prod}/params.yml` stores environment-specific non-secret settings.
- System environment variables override everything.

Examples:

```bash
cp .env.example .env
make config-check
```

Secrets that belong in `.env`:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `API_KEY`
- `SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- database URLs and credentials

Non-secret runtime parameters that belong in `params/`:

- `APP_ENV`
- log level
- CORS origins
- feature flags
- execution limits
- enabled/disabled integrations

For complete details, see [docs/configuration.md](docs/configuration.md) and [docs/standards/configuration-standards.md](docs/standards/configuration-standards.md).

## Integrations

### Telegram

The Telegram integration supports webhook handling, allowlist checks, signature validation, command routing, and message forwarding to agents.

Relevant endpoints:

- `POST /api/telegram/webhook`
- `POST /api/telegram/message`
- `GET /api/telegram/status`

### MCP

The MCP layer exposes registered tools and resources through HTTP endpoints.

Relevant endpoints:

- `GET /api/mcp/info`
- `GET /api/mcp/tools`
- `GET /api/mcp/resources`
- `POST /api/mcp/tools/call`

### Supabase

Supabase is integrated as optional infrastructure and remains disabled by default.

Implemented Supabase support:

- Lazy anon and service-role client factories
- In-memory repositories for default local development
- Supabase-backed repositories for conversations, messages, agent snapshots, skill runs, audit events, and file metadata
- Versioned schema and baseline RLS policies under `supabase/migrations/`
- Optional Storage helper for upload, download, and signed URLs
- Optional Supabase Auth dependency for FastAPI routes that need Bearer-token user context
- Optional integration tests gated by `SUPABASE_TESTS=true`

Local commands:

```bash
make supabase-start
make supabase-status
make supabase-reset
make supabase-stop
```

Supabase remains infrastructure, not agent logic. Agents, skills, API routes, Telegram handlers, and MCP handlers should use repository interfaces or integration services instead of importing the Supabase SDK directly.

For setup and security guidance, see [docs/standards/supabase-integration-guide.md](docs/standards/supabase-integration-guide.md).

### OpenRouter / OpenAI / DeepSeek

LLM providers are selected through configuration and isolated behind the provider abstraction in `app/providers/`.

## Security Guardrails

The template includes:

- API key protection for sensitive POST endpoints
- Telegram user allowlist support
- Telegram webhook signature verification
- CORS restrictions without wildcard defaults
- `ALLOWED_HOSTS` enforcement through trusted host middleware
- Safe secret masking for logs
- Input/output size limits
- Agent timeout limits
- Model/tool/turn execution limits
- Loop detection for repeated runaway turns

Security standards are documented in [docs/standards/security-standards.md](docs/standards/security-standards.md).

## API Endpoints

Health:

- `GET /api/health/health`
- `GET /api/health/info`

Agents:

- `GET /api/agents`
- `GET /api/agents/{agent_id}`
- `POST /api/agents/run`
- `POST /api/agents/{agent_id}/run`
- `POST /api/agents/{agent_id}/reset`

MCP:

- `GET /api/mcp/info`
- `GET /api/mcp/tools`
- `GET /api/mcp/resources`
- `POST /api/mcp/tools/call`

Telegram:

- `POST /api/telegram/webhook`
- `POST /api/telegram/message`
- `GET /api/telegram/status`

## Development

```bash
make install-dev
make config-check
make run-api
make test
```

Additional commands:

```bash
make lint
make format
make clean
```

Supabase local development:

```bash
make supabase-start
make supabase-reset
make supabase-status
make supabase-stop
```

## Project Status

This repository is a v0.4 technical template: usable, structured, and tested, with optional Supabase persistence infrastructure, but not production-battle-tested.

It is intended as a strong starting point, not a finished product. Before production use, review deployment security, observability, persistence, operational runbooks, and the specific risks of your agent domain.

Known template-level follow-up:

- Add production-grade MCP business tools
- Decide the removal timeline for deprecated `BaseAgent`
- Complete or trim unused future-facing areas such as `TurnMode.AGENTIC`, `TurnMode.STREAMING`, and partial snapshots
- Add observability and production telemetry when there is a concrete deployment target

## Reports

- [reports/architecture_audit.md](reports/architecture_audit.md)

## License

MIT. See [LICENSE](LICENSE).
