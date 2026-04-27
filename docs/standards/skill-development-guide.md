# Skill Development Guide

Skills are **reusable, portable capability units** that agents can invoke. A skill encapsulates a single concern (e.g., "search the web", "parse a PDF", "query a database") without depending on the agent that uses it.

---

## Design principles

| Principle | Rule |
|-----------|------|
| **Portable** | A skill must not import or depend on any specific agent class |
| **Single responsibility** | One skill = one capability |
| **Input/output contract** | Skills accept and return plain dicts |
| **No side-effects on agent state** | Skills do not write to agent memory — the agent does |
| **No secrets inside skill code** | Use `settings` or inject via constructor |

---

## Folder layout

```
app/skills/
└── my_skill/
    ├── __init__.py
    └── skill.py          # Skill implementation
```

---

## Implementing a skill

```python
# app/skills/web_search/skill.py
from app.skills.base.skill import BaseSkill

class WebSearchSkill(BaseSkill):
    """Search the web and return result snippets."""

    def __init__(self):
        super().__init__(
            name="web-search",
            description="Search the web and return top snippets.",
        )

    def run(self, input_data: dict) -> dict:
        query = input_data.get("query", "").strip()
        max_results = int(input_data.get("max_results", 5))

        if not query:
            return {"error": "query is required"}

        # Implementation here — call external API, parse response, return
        return {
            "query": query,
            "max_results": max_results,
            "results": [],
        }
```

### Rules for `run()`

- **Sync contract** — use `def run(self, input_data: dict) -> dict`
- **Single input object** — all inputs live under `input_data`
- **Return plain data** — dict values should be JSON-serialisable
- **Raise on unrecoverable errors** — caller (agent) handles exceptions
- **No logging of secrets** — log operation context, never parameter values that may contain PII

---

## Using a skill in an agent

```python
from app.agents.base import ConfiguredAgent
from app.skills.web_search.skill import WebSearchSkill
from app.agents.base.types import TurnResult

class ResearchAgent(ConfiguredAgent):
    def __init__(self):
        super().__init__(
            agent_id="research",
            name="Research Agent",
            system_prompt="You are a research assistant.",
        )
        self.web_search = WebSearchSkill()

    async def run_turn(self, user_input: str) -> TurnResult:
        results = self.web_search.run({"query": user_input, "max_results": 5})
        # Build context from results, call LLM, return TurnResult
        ...
```

---

## Exposing a skill as an MCP tool

If a skill should be accessible externally (via MCP), wrap it in an MCP route handler. See [mcp-integration-guide.md](mcp-integration-guide.md) for the full pattern.

The key rule: **MCP is the transport layer** — the skill itself stays independent.

---

## Input validation

Use Pydantic for structured inputs when a skill is called from MCP or HTTP:

```python
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)
```

Validate at the boundary (route handler or MCP handler), not inside the skill itself.

---

## Testing skills

Test skills in isolation — no agent, no HTTP layer:

```python
import pytest
from app.skills.web_search.skill import WebSearchSkill

def test_web_search_returns_results():
    skill = WebSearchSkill()
    result = skill.run({"query": "Python asyncio", "max_results": 5})
    assert isinstance(result, dict)
    assert "results" in result
```

---

## Compatibility with agentskills.io / agentic-cowork-hub

Skills intended for the public registry must additionally:

1. Expose a `name` class attribute (slug, lowercase, hyphenated)
2. Expose a `description` class attribute (one sentence)
3. Accept all inputs via a single `input_data` dict
4. Return JSON-serialisable output only
5. Include a `requirements.txt` or `pyproject.toml` dependency block if the skill has additional dependencies
