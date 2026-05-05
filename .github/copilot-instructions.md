# GitHub Copilot Instructions

> Coding style and architecture constraints for this repository.

---

## Architecture constraints

- **ADK-first:** Every agent must be a `ConfiguredAgent` subclass in `app/agents/`. Never call LLM providers directly from routes, handlers, or tests.
- **Skills are portable:** `app/skills/` code must never import from `app/agents/`. Skills are agent-agnostic.
- **MCP is transport:** MCP routes in `app/api/routes/mcp.py` call skills. Skills do not call MCP.
- **FastAPI is thin:** Route handlers validate input, call the appropriate agent/skill, and return results. No business logic in routes.

---

## Security non-negotiables

- Protected endpoints under `/api/agents/*`, `/api/mcp/*`, and non-webhook Telegram routes must include `auth_context: AuthContext = Depends(get_auth_context)`
- `POST /api/telegram/webhook` is the explicit exception and must keep Telegram signature plus allowlist security
- CORS `allow_origins` must never include `"*"`
- Secrets must never appear in logs — use `mask_secret()` or `safe_repr_settings()`
- Non-secret config variables must be added to `params/base/params.yml` (and env overrides as needed); secret variables must appear in `.env.example`
- `hmac.compare_digest()` for any secret string comparison — never `==`

---

## Coding style

- **Python 3.12** — use `match`, `type X = ...`, `asyncio.TaskGroup` where appropriate
- **Pydantic v2** — use `model_config`, `Field(...)`, `model_validator(mode="after")`
- **Async by default for agents** — agent turn methods are `async def`; skills use `def run(self, input_data: dict) -> dict`
- **Explicit types** — all function parameters and return types annotated
- **No bare `except`** — always catch specific exceptions
- **Lazy imports for settings** — import `settings` inside function body to avoid circular imports:
  ```python
  def my_func():
      from app.core.config import settings
      return settings.SOME_VALUE
  ```
- **`get_logger(__name__)`** — use structured logging from `app.core.logging`

---

## Naming conventions

| What | Convention | Example |
|------|-----------|---------|
| Agent class | `PascalCase + Agent` | `InvoiceAgent` |
| Agent ID | `kebab-case` | `"invoice-agent"` |
| Skill class | `PascalCase + Skill` | `WebSearchSkill` |
| Route files | `snake_case.py` | `agent.py`, `mcp.py` |
| Test files | `test_<module>.py` | `test_security_guardrails.py` |
| Config vars | `UPPER_SNAKE_CASE` | `MAX_AGENT_TURNS` |

---

## Test expectations

- Tests go in `tests/` at the root
- Use `pytest` — no unittest.TestCase (use plain functions or classes without inheriting)
- Mock settings with `unittest.mock.patch("app.core.config.settings")`
- Mock settings in `app.main` with `patch("app.main.settings")` for CORS/startup tests
- Every new agent: at least one test for `run_turn()` with a mock provider
- Every new endpoint: test with valid auth, missing auth, and invalid input
- Use `pytest.mark.asyncio` for async tests

---

## What to never do

- Do not widen execution limits without documenting the justification in `docs/decisions/`
- Do not add `allow_origins=["*"]` anywhere
- Do not print or log `settings.API_KEY`, `settings.TELEGRAM_BOT_TOKEN`, or any `*_KEY` / `*_SECRET` / `*_TOKEN` field
- Do not bypass `get_auth_context` on protected endpoints
- Do not modify `app/agents/base/` unless implementing a framework feature (not an agent feature)
- Do not hardcode model names — use `settings.LLM_MODEL`

---

## Common patterns

### Adding an agent

```python
from app.agents.base import ConfiguredAgent
from app.agents.base.types import TurnResult

class MyAgent(ConfiguredAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="You are...",
        )
```

### Adding a protected endpoint

```python
from app.api.deps import get_auth_context
from app.auth.context import AuthContext
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/my-endpoint")
async def my_handler(
    request: MyRequest,
    auth_context: AuthContext = Depends(get_auth_context),
):
    ...
```

### Safe logging

```python
from app.core.logging import get_logger
from app.core.security import mask_secret

logger = get_logger(__name__)
logger.info(f"Key configured: {mask_secret(settings.API_KEY)}")
```

### Skill implementation

```python
class MySkill:
    name = "my_skill"
    description = "One sentence description."

    def run(self, input_data: dict) -> dict:
        ...
        return {"result": ...}
```
