# Personal Agent Runtime

**agentic-core-template** — A reusable base repository for agent development, compatible with **agentic-cowork-hub** skills and architecture.

## Overview

Personal Agent Runtime provides a modular foundation for building, deploying, and managing AI agents. It enables:

- **Creating ADK-style agents** with LLM provider abstraction
- **Building and reusing skills** compatible with agentic-cowork-hub
- **Exposing capabilities via MCP** (Model Context Protocol)
- **Multiple LLM provider support** (OpenRouter, OpenAI)
- **Multiple entry points** (FastAPI, CLI, Telegram)
- **Optional Supabase/PostgreSQL integration**

## Architecture

```
personal-agent-runtime/
├── app/
│   ├── api/                    # FastAPI endpoints
│   │   ├── routes/
│   │   │   ├── health.py       # Health checks
│   │   │   ├── agent.py        # Agent execution
│   │   │   ├── mcp.py          # MCP tools
│   │   │   └── telegram.py     # Telegram webhook
│   │   └── deps.py             # Dependencies
│   ├── agents/                 # ADK-style agents
│   │   ├── base_agent.py
│   │   └── registry.py
│   ├── skills/                 # Skills (compatible with agentic-cowork-hub)
│   │   ├── base/
│   │   │   ├── skill.py        # BaseSkill interface
│   │   │   └── registry.py     # Skill registry
│   │   └── examples/
│   │       ├── calculator.py
│   │       └── text_processor.py
│   ├── mcp/                    # MCP exposure layer
│   │   └── tool_registry.py
│   ├── providers/              # LLM abstraction
│   │   ├── base.py
│   │   ├── openrouter.py
│   │   ├── openai.py
│   │   └── factory.py
│   ├── integrations/
│   │   └── telegram/           # Telegram bot
│   │       ├── bot.py
│   │       ├── handlers.py
│   │       └── schemas.py
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── logging.py          # Logging setup
│   │   └── security.py         # Security utilities
│   ├── db/
│   │   ├── session.py          # Database session
│   │   └── models/
│   └── main.py                 # FastAPI app
├── examples/
│   └── invoice_agent/          # Example agent
├── scripts/
│   ├── run_api.sh
│   ├── run_agent.sh
│   └── run_mcp.sh
├── tests/
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

## Quick Start

### 1. Setup

Clone or initialize the repository:

```bash
cd agentic-core-template
```

Install dependencies:

```bash
make install-dev
```

Configure environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configure LLM Provider

Set your LLM provider and API key in `.env`:

```bash
LLM_PROVIDER=openrouter  # or 'openai'
LLM_MODEL=meta-llama/llama-3.1-70b-instruct
OPENROUTER_API_KEY=your-api-key
```

### 3. Run API Server

```bash
make run-api
```

The API will be available at `http://localhost:8000`.

- **Health check**: `GET /api/health/health`
- **API docs**: `GET /docs`

### 4. Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/api/health/health
```

#### Run Agent
```bash
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "default",
    "input": "What is 2 + 2?",
    "system_prompt": "You are a helpful assistant."
  }'
```

#### List Available Agents
```bash
curl http://localhost:8000/api/agents
```

#### MCP Tools
```bash
curl http://localhost:8000/api/mcp/tools
```

## Key Components

### Agents

Agents are the main execution units. Create a new agent:

```python
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="You are helpful.",
        )

# Register and use
from app.agents.registry import get_registry
registry = get_registry()
registry.register("my-agent", MyAgent)

agent = registry.instantiate("my-agent", agent_id="my-agent")
response = agent.run("Hello!")
```

### Skills

Skills are reusable units of work, compatible with **agentic-cowork-hub**:

```python
from app.skills.base.skill import BaseSkill

class MySkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="my-skill",
            description="Does something useful",
        )
    
    def run(self, input_data: dict) -> dict:
        # Implement skill logic
        return {"result": "output"}

# Use the skill
skill = MySkill()
result = skill.run({"param": "value"})
```

### LLM Providers

Providers are abstracted through a factory:

```python
from app.providers.factory import get_llm_provider

provider = get_llm_provider()  # Uses LLM_PROVIDER env var

# Generate text
response = await provider.generate(
    prompt="What is AI?",
    system_prompt="You are knowledgeable.",
)

# Call with tools
response = await provider.generate_with_tools(
    prompt="Calculate 2+2",
    tools=[...]
)
```

### MCP Integration

Expose agent capabilities via MCP:

```python
from app.mcp.tool_registry import get_mcp_server

server = get_mcp_server()

# Register a tool
server.register_tool(
    tool_id="my-tool",
    description="Does something",
    input_schema={"type": "object", "properties": {}},
    handler=my_handler_function,
)

# List tools
tools = server.list_tools()
```

### Telegram Bot

Enable Telegram integration by setting:

```bash
TELEGRAM_ENABLED=True
TELEGRAM_BOT_TOKEN=your-bot-token
```

Messages are automatically routed to agents.

**Webhook setup** (if using Telegram webhooks):

```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d "url=https://your-domain/api/telegram/webhook"
```

## Configuration

Personal Agent Runtime uses **layered environment configuration** for flexible deployment across development, staging, and production environments.

### Quick Setup

```bash
# Create configuration from examples
cp .env.base.example .env.base      # Common configuration
cp .env.dev.example .env.dev        # Development overrides
touch .env.local                    # Local secrets (git-ignored)

# Add your secrets to .env.local (never commit these)
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" >> .env.local
echo "TELEGRAM_BOT_TOKEN=123456:ABCDEF" >> .env.local

# Verify configuration is valid
make config-check
```

### How Configuration Works

Configuration is loaded in priority order (highest priority last):

1. **.env.base** — Common base configuration (versioned)
2. **.env.{APP_ENV}** — Environment overrides (dev/pre/prod, versioned as examples)
3. **.env.local** — Local secrets (NOT versioned, git-ignored)
4. **System environment variables** — Override everything (highest priority)

### Configuration Validation

Run diagnostics to verify your configuration:

```bash
make config-check
```

Shows active environment, enabled features, and validation status.

### For Complete Configuration Documentation

See [docs/configuration.md](docs/configuration.md) for:
- Detailed setup instructions per environment
- All configuration fields reference
- Best practices for secrets management
- CI/CD integration examples
- Troubleshooting guide

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | dev | Environment (dev/pre/prod) |
| `LLM_PROVIDER` | openrouter | LLM provider (openrouter, openai) |
| `LLM_MODEL` | meta-llama/llama-3.1-70b-instruct | Model identifier |
| `OPENROUTER_API_KEY` | - | OpenRouter API key |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `TELEGRAM_ENABLED` | False | Enable Telegram bot |
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token |
| `SUPABASE_ENABLED` | False | Enable Supabase |
| `SUPABASE_URL` | - | Supabase project URL |
| `MCP_ENABLED` | False | Enable MCP server |
| `LOG_LEVEL` | INFO | Logging verbosity |

## API Endpoints

### Health & Info
- `GET /api/health/health` — Health status
- `GET /api/health/info` — Application info

### Agents
- `GET /api/agents` — List available agents
- `GET /api/agents/{agent_id}` — Agent info
- `POST /api/agents/run` — Run an agent with `agent_id` in body
- `POST /api/agents/{agent_id}/run` — Run an agent by route ID

### MCP
- `GET /api/mcp/info` — Server info
- `GET /api/mcp/tools` — List tools
- `GET /api/mcp/resources` — List resources
- `POST /api/mcp/tools/call` — Call a tool

### Telegram
- `POST /api/telegram/webhook` — Telegram webhook
- `POST /api/telegram/message` — Send message
- `GET /api/telegram/status` — Bot status

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | System architecture, layers, and data flow |
| [docs/decisions/0001-adk-first-runtime.md](docs/decisions/0001-adk-first-runtime.md) | ADR: why ADK over LangChain/CrewAI |
| [docs/standards/agent-development-guide.md](docs/standards/agent-development-guide.md) | How to create and register agents |
| [docs/standards/skill-development-guide.md](docs/standards/skill-development-guide.md) | How to build portable skills |
| [docs/standards/mcp-integration-guide.md](docs/standards/mcp-integration-guide.md) | Exposing skills via MCP |
| [docs/standards/client-integration-guide.md](docs/standards/client-integration-guide.md) | REST API, Telegram, and future clients |
| [docs/standards/configuration-standards.md](docs/standards/configuration-standards.md) | Layered env config, all variables |
| [docs/standards/security-standards.md](docs/standards/security-standards.md) | API key auth, CORS, safe logging |
| [AGENTS.md](AGENTS.md) | AI agent coding context and constraints |
| [.codex/PROJECT_CONTEXT.md](.codex/PROJECT_CONTEXT.md) | Codex project context and folder map |

---

## Development

### Lint & Format
```bash
make lint      # Check code
make format    # Format code
```

### Run Tests
```bash
make test
# or
python -m pytest
```

---

## Skills Compatibility with agentic-cowork-hub

This project is designed to be fully compatible with **agentic-cowork-hub** skills:

1. **Same BaseSkill interface** — Skills written for one platform work in both
2. **No strong coupling** — Skills are independent modules
3. **Shared tool registry** — MCP tools and shared skills can be imported across projects

To use skills from agentic-cowork-hub:

```python
# Import directly
from agentic_cowork_hub.tools.portfolio_tools import get_portfolio_positions

# Register in your runtime
from app.skills.base.registry import get_registry
registry = get_registry()
# ... adapt as needed
```

## Future Extensions

Not in this scaffold but roadmap:

- [ ] RAG layer
- [ ] Vector database integration
- [ ] Observability / telemetry
- [ ] Advanced authentication
- [ ] UI frontend
- [ ] Multi-agent orchestration
- [ ] Persistent memory service

## Design Principles

- **KISS** — Keep it simple and straightforward
- **YAGNI** — You aren't gonna need it (avoid over-engineering)
- **Modularity** — Clear separation of concerns
- **Composability** — Easy to combine skills and agents
- **Compatibility** — Works with agentic-cowork-hub ecosystem

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For questions and issues, please refer to the project documentation or open an issue.

---

**Built with ❤️ for agentic development**
