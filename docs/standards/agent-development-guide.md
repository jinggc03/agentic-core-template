# Agent Development Guide

Agents in this repository follow the **ADK-first pattern**: every agent is a `ConfiguredAgent` subclass that executes work in a structured five-step turn.

---

## Folder layout

```
app/agents/
├── base/                   # ADK framework — do not modify for individual agents
│   ├── configured_agent.py
│   ├── execution_policy.py
│   ├── loop_guard.py
│   └── types.py
├── registry.py             # Global agent registry
└── <your_agent>/           # One folder per agent
    ├── __init__.py
    ├── agent.py            # Subclass of ConfiguredAgent
    └── context.py          # Agent-specific state (optional)

examples/
└── invoice_agent/          # Reference implementation
```

---

## Five-step turn pattern

Every `run_turn()` call in `ConfiguredAgent` follows this fixed sequence:

| Step | Name | What happens |
|------|------|-------------|
| 1 | **Routing** | Policy enforcer validates whether the turn is allowed |
| 2 | **Context** | Agent state / history is gathered and injected |
| 3 | **Message building** | User input is formatted into the provider message format |
| 4 | **Execution** | LLM provider is called with a timeout guard |
| 5 | **State update** | Output is stored, loop guard is updated, turn recorded |

Execution limits are applied at steps 1 and 4:
- Input length guard (step 1)
- LLM timeout via `asyncio.wait_for` (step 4)
- Output truncation (step 4 → 5)
- Loop detection at input and output stages

---

## Creating a new agent

### 1. Create the agent folder

```
app/agents/my_agent/
├── __init__.py
└── agent.py
```

### 2. Subclass `ConfiguredAgent`

```python
# app/agents/my_agent/agent.py
from app.agents.base import ConfiguredAgent

class MyAgent(ConfiguredAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="You are a helpful assistant that...",
        )

    # Override only if you need custom turn behaviour:
    # async def run_turn(self, user_input: str) -> TurnResult: ...
```

### 3. Register the agent

```python
# app/agents/registry.py  (add one line)
from app.agents.my_agent.agent import MyAgent

AGENT_REGISTRY = {
    "invoice": InvoiceAgent,
    "my-agent": MyAgent,   # ← add here
}
```

### 4. Done

The agent is now accessible via:
- `GET /api/agents` — lists all agents
- `POST /api/agents/run` with `{"agent_id": "my-agent", "input": "..."}`
- `POST /api/agents/{agent_id}/run` with `{"input": "..."}`

---

## Execution policy

Agents inherit the global policy from `settings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_MODEL_CALLS_PER_TURN` | 1 | LLM calls per user turn |
| `MAX_TOOL_CALLS_PER_TURN` | 5 | Tool calls per turn |
| `MAX_AGENT_TURNS` | 10 | Turns per conversation session |
| `MAX_INPUT_CHARS` | 8000 | Max user input length |
| `MAX_OUTPUT_CHARS` | 12000 | Max output length (truncated if exceeded) |
| `AGENT_TIMEOUT_SECONDS` | 60 | Timeout for LLM call |

To override per-agent, pass a custom `ExecutionPolicy` to the constructor:

```python
from app.agents.base import ConfiguredAgent
from app.agents.base.execution_policy import ExecutionPolicy, ToolScope

class MyAgent(ConfiguredAgent):
    def __init__(self):
        policy = ExecutionPolicy(
            max_model_calls=2,
            max_tool_calls=10,
            timeout_seconds=30,
        )
        super().__init__(
            agent_id="my-agent",
            name="My Agent",
            system_prompt="...",
            policy=policy,
        )
```

---

## Loop guard

Each agent instance holds a `LoopGuard` that detects:

- Identical user input repeated ≥ 3 consecutive turns
- Same tool called ≥ 5 consecutive times
- Identical output repeated ≥ 3 consecutive turns

When a loop is detected, `run_turn()` returns `TurnResult(success=False, error="Loop detected...")` without calling the LLM. The guard is reset when `agent.reset()` is called.

---

## Testing your agent

Add tests under `tests/` that:

1. Construct the agent directly (no HTTP layer)
2. Call `run_turn()` with mock provider responses
3. Assert `TurnResult.success`, `TurnResult.output`, and state changes

See `tests/test_adk_architecture.py` for examples.

---

## Rules

- Every new agent **must** be a `ConfiguredAgent` subclass
- `BaseAgent` is **deprecated** and only available for backward compatibility
- **Never** hardcode secrets or API keys — use `settings`
- **Never** bypass the execution policy limits
- Every new agent **must** have at least one test
- System prompts must not contain user-provided data — build them in `run_turn()` if dynamic
