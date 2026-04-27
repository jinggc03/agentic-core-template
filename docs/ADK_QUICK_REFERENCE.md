# ADK Quick Reference

> **v0.3 note:** `BaseAgent` is deprecated — use `ConfiguredAgent` for all new agents.

## Agent Creation Template

```python
# 1. Define types (types.py)
class MyState(BaseModel):
    field1: str = None
    field2: int = None

# 2. Routing (routing.py)
class MyRouter:
    def resolve_mode(self, input, context) -> TurnMode:
        return TurnMode.SINGLE
    
    def get_next_step(self, input, context) -> str:
        return "process"

# 3. Context (context.py)
class MyContextManager:
    def __init__(self):
        self.context = MyState()
    
    def should_call_llm(self) -> bool:
        return True

# 4. Messages (message_builders.py)
class MyMessageBuilder:
    @staticmethod
    def build_system_prompt(mode) -> str:
        return "You are helpful..."
    
    @staticmethod
    def build_prompt(user_input, context, task) -> str:
        return f"Task: {task}\nInput: {user_input}"

# 5. Agent (agent.py)
# NOTE: BaseAgent is deprecated. Always extend ConfiguredAgent.
class MyAgent(ConfiguredAgent):
    def __init__(self, agent_id="my-agent", **kwargs):
        super().__init__(agent_id, **kwargs)
        self.router = MyRouter()
        self.context_manager = MyContextManager()
        self.message_builder = MyMessageBuilder()
    
    async def run_turn(self, user_input: str) -> TurnResult:
        import time
        start = time.time()
        try:
            # 1. Routing
            mode = self.router.resolve_mode(user_input, self.context_manager.context)
            
            # 2. Context
            if not self.context_manager.should_call_llm():
                return TurnResult(success=True, output="cached")
            
            # 3. Message building
            prompt = self.message_builder.build_prompt(user_input, self.context_manager.context, "task")
            system = self.message_builder.build_system_prompt(mode)
            
            # 4. Execution
            allowed, error = self.policy_enforcer.on_model_call()
            if not allowed:
                return TurnResult(success=False, error=error)
            
            response = await self.provider.generate(prompt, system_prompt=system)
            
            # 5. State update
            self.messages.append(Message(role="assistant", content=response))
            self.context_manager.context.field1 = response
            
            return TurnResult(
                success=True,
                output=response,
                model_calls=1,
                execution_time_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return TurnResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000
            )
```

## Five-Step Pattern Checklist

```
☐ Step 1: ROUTING
  - Determine execution mode (SINGLE/AGENTIC/STREAMING)
  - Route to next step based on input/context
  - Log routing decision

☐ Step 2: CONTEXT
  - Load context/state
  - Check if LLM call needed
  - Return cached result if available
  - Log context state

☐ Step 3: MESSAGE BUILDING
  - Construct prompt for current task
  - Include relevant context
  - Select system prompt for mode
  - Log prompt summary

☐ Step 4: EXECUTION
  - Check policy enforcement
  - Call LLM provider
  - Update metrics (model_calls, tool_calls)
  - Handle errors gracefully
  - Log execution result

☐ Step 5: STATE UPDATE
  - Save context/state
  - Add messages to history
  - Update snapshot
  - Log state changes
```

## Usage Examples

### Single Turn
```python
agent = MyAgent()
result = await agent.run_turn("Hello")
print(result.output)
```

### Multi-Turn
```python
runner = AgentRunner(MyAgent())
for i in range(3):
    result = await runner.run_turn(f"Input {i}")
    print(result.output)
```

### Via FastAPI
```python
# Run by agent_id in path (preferred)
POST /api/agents/{agent_id}/run
Headers: X-API-Key: <your-key>
{
    "input": "Hello",
    "conversation_id": "conv-123"
}

# Or run with agent_id in body
POST /api/agents/run
Headers: X-API-Key: <your-key>
{
    "agent_id": "my-agent",
    "input": "Hello",
    "conversation_id": "conv-123"
}
```

## Policy Enforcement

### Available Policies
- **Dev**: max_model_calls=10, max_tool_calls=20, turn_limit=1000
- **Pre**: max_model_calls=7, max_tool_calls=15, turn_limit=500
- **Prod**: max_model_calls=5, max_tool_calls=10, turn_limit=100

### Check Before Calls
```python
# Before model call
allowed, error = self.policy_enforcer.on_model_call()
if not allowed:
    return TurnResult(success=False, error=error)

# Before tool call
allowed, error = self.policy_enforcer.on_tool_call()
if not allowed:
    return TurnResult(success=False, error=error)

# At turn start
allowed, error = self.policy_enforcer.on_turn_start()
if not allowed:
    return TurnResult(success=False, error=error)
```

## Registry Usage

```python
from app.agents.registry import get_registry

registry = get_registry()

# List available
print(registry.list_available())  # ['invoice-agent', ...]

# Instantiate
agent = registry.instantiate("invoice-agent", conversation_id="c123")

# Get cached instance
agent = registry.get_instance("invoice-agent")

# Release instance
registry.release_instance("invoice-agent")
```

## Return Value Structure

```python
class TurnResult(BaseModel):
    success: bool               # Whether turn succeeded
    output: str                 # Agent response
    model_calls: int = 0        # LLM calls made
    tool_calls: int = 0         # Tool calls made
    execution_time_ms: float    # Execution time
    error: Optional[str] = None # Error if failed
    metadata: Dict = {}         # Additional data
```

## Context Caching

### Pattern
```python
class ContextManager:
    def should_call_llm_for_extraction(self) -> bool:
        if self.context and self.context.extracted:
            return False  # Already have data
        return True  # Need to call

    def should_call_llm_for_validation(self) -> bool:
        if self.context and self.context.validated:
            return False  # Already validated
        return True
```

### Usage in Agent
```python
if not self.context_manager.should_call_llm_for_extraction():
    # Return cached
    return TurnResult(success=True, output=cached_result)

# Otherwise call LLM
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Model call limit reached (5)` | Exceeded max_model_calls | Increase policy or reduce calls |
| `Tool calls disabled` | tool_scope=NONE | Change policy to INTERNAL or FULL |
| `Turn limit exceeded (100)` | Too many turns | Increase turn_limit or reset agent |
| `context_manager.context is None` | Not loaded | Call load_context() |
| `Timeout after 30s` | Execution too slow | Simplify prompts or increase timeout |

## Testing Template

```python
class TestMyAgent:
    def test_routing(self):
        router = MyRouter()
        mode = router.resolve_mode("input", context)
        assert mode == TurnMode.SINGLE
    
    def test_context(self):
        manager = MyContextManager()
        assert manager.should_call_llm() == True
    
    def test_messages(self):
        prompt = MyMessageBuilder.build_prompt("input", context, "task")
        assert "input" in prompt
    
    async def test_turn(self):
        agent = MyAgent()
        result = await agent.run_turn("input")
        assert result.success
```

## Monitoring Metrics

```python
# After execution
result: TurnResult
print(f"Success: {result.success}")
print(f"LLM calls: {result.model_calls}")
print(f"Tool calls: {result.tool_calls}")
print(f"Time: {result.execution_time_ms}ms")
print(f"Output length: {len(result.output)} chars")

# Multi-turn
summary = runner.get_execution_summary()
print(f"Turns: {summary['turns']}")
print(f"Successful: {summary['successful_turns']}")
print(f"Avg time: {summary['avg_execution_time']}ms")
```

## Deployment

### Register Your Agent
```python
# In app/agents/registry.py or auto-loaded from examples/
from examples.my_agent import MyAgent
registry.register("my-agent", MyAgent)
```

### Available Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/agents/run` | API key | Execute turn (body agent_id) |
| POST | `/api/agents/{id}/run` | API key | Execute turn (path agent_id) |
| GET | `/api/agents` | API key | List agents |
| GET | `/api/agents/{id}` | API key | Agent info |
| GET | `/api/agents/{id}/context` | API key | Get state |
| POST | `/api/agents/{id}/reset` | API key | Reset agent |

## Resources

- **Full Guide**: See `docs/ADK_ARCHITECTURE.md`
- **Example**: See `examples/invoice_agent/`
- **Tests**: See `tests/test_adk_architecture.py`
- **API Docs**: See `app/api/routes/agent.py`
- **Audit**: See `reports/architecture_audit.md`

## Security requirements

- All agent endpoints require `X-API-Key` header.
- Use `Depends(require_api_key)` in every new `POST` route under `/api/`.
- Never log or print API keys; use `mask_secret()` from `app.core.security`.
- `BaseAgent` is deprecated and emits `DeprecationWarning` — migrate to `ConfiguredAgent`.
