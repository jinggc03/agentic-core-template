# ADK Architecture Guide

## Overview

The **ADK (Agent Development Kit)** is our framework for building intelligent agents with structured execution, controlled resource usage, and separation of concerns.

This document describes the ADK architecture, its components, and how to build agents following the ADK pattern.

## Architecture Principles

### 1. Five-Step Turn Execution Pattern
Every agent turn follows this sequence:
```
User Input
    ↓
1. ROUTING - Determine execution mode and flow
    ↓
2. CONTEXT - Load state, prevent unnecessary LLM calls
    ↓
3. MESSAGE BUILDING - Construct optimized prompts
    ↓
4. EXECUTION - Call LLM provider with policy enforcement
    ↓
5. STATE UPDATE - Save context snapshot for next turn
    ↓
Agent Output
```

### 2. Separation of Concerns
Each agent has distinct responsibilities:
- **Routing Layer** (`routing.py`) - Determines execution flow
- **Context Layer** (`context.py`) - Manages state and caching
- **Message Builder** (`message_builders.py`) - Constructs prompts
- **Agent** (`agent.py`) - Orchestrates the five steps
- **Types** (`types.py`) - Domain-specific data models

### 3. Controlled Execution
Policies enforce limits on:
- Model calls per turn
- Tool usage scope
- Total conversation turns
- Execution timeout

### 4. Environment-Based Policies
Different policies for different environments:
- **Dev**: Flexible (10 model calls, 20 tool calls, 1000 turns)
- **Pre-production**: Semi-strict (7 model calls, 15 tool calls, 500 turns)
- **Production**: Strict (5 model calls, 10 tool calls, 100 turns)

## Core Components

### 1. Types System (`app/agents/base/types.py`)

#### Enums
```python
class TurnMode(str, Enum):
    SINGLE = "single"          # Single LLM call
    AGENTIC = "agentic"        # Multi-step with tools
    STREAMING = "streaming"    # Streaming response

class ToolScope(str, Enum):
    NONE = "none"              # No tools
    INTERNAL = "internal"      # Internal tools only
    FULL = "full"              # Full tool access
```

#### Data Models
```python
class Message(BaseModel):
    """Single message in conversation."""
    role: str                   # user/assistant/system/tool
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]

class Snapshot(BaseModel):
    """Agent state snapshot for context caching."""
    agent_id: str
    conversation_id: str
    turn_count: int
    messages: List[Message]
    state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class TurnContext(BaseModel):
    """Input context for a turn."""
    agent_id: str
    conversation_id: str
    turn_count: int
    user_input: str
    system_prompt: str
    mode: TurnMode
    policy: Optional[ExecutionPolicy]
    snapshot: Optional[Snapshot]
    metadata: Dict[str, Any]

class TurnResult(BaseModel):
    """Output result from a turn."""
    success: bool
    output: str
    model_calls: int
    tool_calls: int
    execution_time_ms: float
    error: Optional[str]
    metadata: Dict[str, Any]
```

### 2. Execution Policy (`app/agents/base/execution_policy.py`)

Controls resource usage:
```python
class ExecutionPolicy:
    max_model_calls: int = 5         # LLM calls per turn
    max_tool_calls: int = 10         # Tool calls per turn
    tool_scope: ToolScope = FULL     # Available tools
    turn_limit: int = 100            # Max turns/conversation
    timeout_seconds: int = 30        # Execution timeout

    def is_within_limits(...) -> tuple[bool, Optional[str]]:
        """Check if execution respects policy."""
```

Enforcement via PolicyEnforcer:
```python
class PolicyEnforcer:
    def on_model_call() -> tuple[bool, Optional[str]]:
        """Check before each LLM call."""
    
    def on_tool_call() -> tuple[bool, Optional[str]]:
        """Check before each tool call."""
    
    def on_turn_start() -> tuple[bool, Optional[str]]:
        """Check at turn start."""
```

### 3. ConfiguredAgent (`app/agents/base/configured_agent.py`)

The main ADK agent class:
```python
class ConfiguredAgent:
    agent_id: str
    name: str
    system_prompt: str
    provider: BaseLLMProvider
    policy_enforcer: PolicyEnforcer
    messages: List[Message]         # Conversation history
    turn_count: int
    conversation_id: str

    async def run_turn(user_input: str) -> TurnResult:
        """Execute one turn (5-step pattern)."""
    
    def prepare_turn(user_input: str) -> TurnContext:
        """Prepare turn context."""
    
    def save_snapshot() -> Snapshot:
        """Save state for context caching."""
    
    def reset() -> None:
        """Clear all state."""
```

### 4. AgentRunner (`app/agents/base/runner.py`)

Orchestrates multi-turn execution:
```python
class AgentRunner:
    agent: ConfiguredAgent
    running: bool
    turns_history: List[TurnResult]

    async def run_turn(user_input: str) -> TurnResult:
        """Execute one turn."""
    
    def get_execution_summary() -> Dict:
        """Summary of all executed turns."""
    
    def reset() -> None:
        """Reset agent and history."""
```

### 5. Agent Registry (`app/agents/registry.py`)

Manages agent instances:
```python
class AgentRegistry:
    def register(agent_id: str, agent_class: Type[ConfiguredAgent]):
        """Register agent class."""
    
    def instantiate(agent_id: str, **kwargs) -> ConfiguredAgent:
        """Create agent instance."""
    
    def get_instance(agent_id: str) -> Optional[ConfiguredAgent]:
        """Get cached instance."""
    
    def load_modular_agent(agent_id: str, module_path: str, class_name: str):
        """Load agent from module (e.g., examples.invoice_agent.agent)."""
    
    def discover_agents(package_path: str) -> Dict[str, str]:
        """Discover agents in package."""
```

## Building an ADK Agent

### Directory Structure
```
examples/my_agent/
├── __init__.py                 # Module exports
├── agent.py                    # Main agent class
├── routing.py                  # Routing logic
├── context.py                  # Context management
├── message_builders.py         # Prompt builders
├── types.py                    # Domain types
└── prompt.md                   # Prompt documentation
```

### Step 1: Define Domain Types (`types.py`)
```python
from pydantic import BaseModel, Field

class MyData(BaseModel):
    """Domain-specific data."""
    field1: str
    field2: int

class MyContext(BaseModel):
    """Agent state."""
    data: Optional[MyData] = None
    processed: bool = False
```

### Step 2: Implement Routing (`routing.py`)
```python
from app.agents.base import TurnMode

class MyRouter:
    def resolve_mode(self, user_input: str, context: MyContext) -> TurnMode:
        """Determine execution mode."""
        if len(user_input) > 100:
            return TurnMode.AGENTIC
        return TurnMode.SINGLE
    
    def get_next_step(self, user_input: str, context: MyContext) -> str:
        """Route to next step."""
        if not context.data:
            return "extract"
        return "process"
```

### Step 3: Implement Context Manager (`context.py`)
```python
class MyContextManager:
    def __init__(self):
        self.context: Optional[MyContext] = None
    
    def load_context(self, conversation_id: str):
        """Load context from cache."""
        # Load from storage
        pass
    
    def save_context(self):
        """Save context."""
        # Save to storage
        pass
    
    def should_call_llm(self) -> bool:
        """Avoid LLM calls if possible."""
        if self.context and self.context.processed:
            return False
        return True
```

### Step 4: Implement Message Builders (`message_builders.py`)
```python
from app.agents.base import Message, TurnMode

class MyMessageBuilder:
    @staticmethod
    def build_system_prompt(mode: TurnMode) -> str:
        """System prompt per mode."""
        return "You are a helpful assistant..."
    
    @staticmethod
    def build_extraction_prompt(user_input: str) -> Message:
        """Prompt for extraction task."""
        return Message(
            role="user",
            content=f"Extract from: {user_input}"
        )
    
    @staticmethod
    def build_context_message(
        user_input: str,
        context: MyContext,
        task: str
    ) -> Message:
        """Prompt including context."""
        ctx_text = json.dumps(context.dict())
        return Message(
            role="user",
            content=f"Context: {ctx_text}\n\nTask: {task}\n\nInput: {user_input}"
        )
```

### Step 5: Implement Agent (`agent.py`)
```python
from app.agents.base import ConfiguredAgent, TurnResult

class MyAgent(ConfiguredAgent):
    def __init__(self, agent_id="my-agent", **kwargs):
        super().__init__(agent_id=agent_id, **kwargs)
        self.router = MyRouter()
        self.context_manager = MyContextManager()
        self.message_builder = MyMessageBuilder()
    
    async def run_turn(self, user_input: str) -> TurnResult:
        import time
        start = time.time()
        
        try:
            # Step 1: ROUTING
            logger.debug("Step 1: Routing...")
            mode = self.router.resolve_mode(user_input, self.context_manager.context)
            
            # Step 2: CONTEXT
            logger.debug("Step 2: Context...")
            self.context_manager.load_context(self.conversation_id)
            if not self.context_manager.should_call_llm():
                return TurnResult(
                    success=True,
                    output="Cached result",
                    execution_time_ms=(time.time() - start) * 1000
                )
            
            # Step 3: MESSAGE BUILDING
            logger.debug("Step 3: Message building...")
            message = self.message_builder.build_context_message(
                user_input,
                self.context_manager.context,
                "process"
            )
            system_prompt = self.message_builder.build_system_prompt(mode)
            
            # Step 4: EXECUTION (with policy enforcement)
            logger.debug("Step 4: Execution...")
            allowed, error = self.policy_enforcer.on_model_call()
            if not allowed:
                return TurnResult(
                    success=False,
                    output="",
                    error=error,
                    execution_time_ms=(time.time() - start) * 1000
                )
            
            response = await self.provider.generate(
                prompt=message.content,
                system_prompt=system_prompt
            )
            
            # Step 5: STATE UPDATE
            logger.debug("Step 5: State update...")
            self.messages.append(Message(role="user", content=user_input))
            self.messages.append(Message(role="assistant", content=response))
            self.context_manager.save_context()
            
            return TurnResult(
                success=True,
                output=response,
                model_calls=1,
                execution_time_ms=(time.time() - start) * 1000
            )
        
        except Exception as e:
            logger.error(f"Turn failed: {e}")
            return TurnResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000
            )
```

### Step 6: Create Module Exports (`__init__.py`)
```python
from .agent import MyAgent
from .routing import MyRouter
from .context import MyContextManager
from .message_builders import MyMessageBuilder
from .types import MyData, MyContext

__all__ = [
    "MyAgent",
    "MyRouter",
    "MyContextManager",
    "MyMessageBuilder",
    "MyData",
    "MyContext",
]
```

## Using ADK Agents

### Instantiation via Registry
```python
from app.agents.registry import get_registry

registry = get_registry()

# Instantiate agent
agent = registry.instantiate(
    "my-agent",
    conversation_id="conv-123"
)
```

### Single Turn Execution
```python
result: TurnResult = await agent.run_turn("Hello")

print(f"Success: {result.success}")
print(f"Output: {result.output}")
print(f"Model calls: {result.model_calls}")
print(f"Time: {result.execution_time_ms}ms")
```

### Multi-Turn Execution
```python
from app.agents.base import AgentRunner

runner = AgentRunner(agent)

# Execute multiple turns
for i in range(3):
    result = await runner.run_turn(f"Input {i}")
    print(f"Turn {i}: {result.output}")

# Get summary
summary = runner.get_execution_summary()
print(f"Total turns: {summary['turns']}")
print(f"Successful: {summary['successful_turns']}")
```

### Via FastAPI
```python
# POST /api/agents/run
{
    "agent_id": "my-agent",
    "input": "Hello",
    "conversation_id": "conv-123"
}

# Response
{
    "agent_id": "my-agent",
    "output": "Hi! How can I help?",
    "status": "success",
    "execution_time_ms": 234.5,
    "model_calls": 1,
    "tool_calls": 0
}
```

## Environment-Based Policies

### Configuration
```python
from app.agents.base import ExecutionPolicy, get_default_policy
from app.core.config import settings

# Get environment-specific policy
policy = get_default_policy(settings.APP_ENV)

# Or customize
dev_policy = ExecutionPolicy(
    max_model_calls=10,
    max_tool_calls=20,
    turn_limit=1000,
    timeout_seconds=60
)
```

### Enforcement
The PolicyEnforcer automatically:
1. Tracks model calls per turn
2. Tracks tool calls per turn
3. Enforces turn limits
4. Prevents disabled tools (tool_scope=NONE)
5. Rejects calls exceeding limits

## Context Caching Pattern

### Avoid Redundant LLM Calls
```python
class InvoiceContextManager:
    def should_call_llm_for_extraction(self) -> bool:
        """Skip LLM if invoice already extracted."""
        if self.context and self.context.invoice_data:
            return False  # Already have data
        return True  # Need to call LLM
    
    def should_call_llm_for_validation(self) -> bool:
        """Skip if already validated."""
        if self.context and self.context.is_validated:
            return False
        return True
```

Usage:
```python
if not context_manager.should_call_llm_for_extraction():
    # Return cached result
    return TurnResult(
        success=True,
        output="Cached invoice data"
    )
```

## Message Building Best Practices

### Task-Specific Prompts
```python
class MessageBuilder:
    @staticmethod
    def build_extraction_prompt(user_input: str) -> str:
        """Optimized prompt for extraction."""
        return f"""Extract structured data from:
        
{user_input}

Return JSON with fields: ..."""
    
    @staticmethod
    def build_validation_prompt(invoice: Invoice) -> str:
        """Optimized prompt for validation."""
        return f"""Validate invoice:

{invoice.json()}

Check for: completeness, consistency, anomalies..."""
```

### Context Inclusion
```python
@staticmethod
def build_context_message(user_input: str, context: State, task: str):
    """Include context to avoid re-explaining."""
    return f"""
CONTEXT:
{json.dumps(context.dict())}

TASK: {task}

INPUT: {user_input}
"""
```

## Testing ADK Agents

### Unit Tests
```python
def test_agent_routing():
    """Test routing layer."""
    router = MyRouter()
    mode = router.resolve_mode("long input" * 50, context)
    assert mode == TurnMode.AGENTIC

def test_agent_context_caching():
    """Test context caching."""
    manager = MyContextManager()
    manager.context = MyContext(processed=True)
    assert not manager.should_call_llm()

def test_agent_turn():
    """Test full turn."""
    agent = MyAgent()
    result = await agent.run_turn("Hello")
    assert result.success
    assert result.output
```

### Integration Tests
```python
def test_agent_multi_turn():
    """Test multi-turn conversation."""
    runner = AgentRunner(MyAgent())
    
    for i in range(3):
        result = await runner.run_turn(f"Input {i}")
        assert result.success
    
    summary = runner.get_execution_summary()
    assert summary['turns'] == 3
```

## Backward Compatibility

### Using Legacy BaseAgent API
```python
from app.agents.base_agent import BaseAgent

# Still works - wraps ConfiguredAgent
agent = BaseAgent(
    agent_id="legacy-agent",
    name="Legacy Agent",
    system_prompt="You are helpful"
)

output = agent.run("Hello")  # Sync API
```

## Example: Invoice Agent

Full example implementing the ADK pattern for invoice processing:

**Path**: `examples/invoice_agent/`

Key features:
- Routing: Extract → Validate → Summarize
- Context: Cache invoice data to avoid re-processing
- Messages: Task-specific prompts
- Execution: 5-step pattern with logging at each step
- Tests: Comprehensive test coverage

See `examples/invoice_agent/` for complete implementation.

## Best Practices

1. **Separate Concerns** - Keep routing, context, messaging separate
2. **Cache When Possible** - Use context manager to avoid LLM calls
3. **Log Each Step** - Debug logs at routing/context/building/execution
4. **Test Each Layer** - Unit test router, context, messages separately
5. **Use Type Safety** - Define domain types with Pydantic
6. **Honor Policies** - Always check policy enforcement before external calls
7. **Save State** - Update context snapshot at end of turn
8. **Handle Errors** - Return TurnResult with error messages
9. **Measure Performance** - Track execution_time_ms in each result
10. **Document Prompts** - Create prompt.md explaining your agent's prompts

## Common Patterns

### Pattern 1: Keyword Routing
```python
def resolve_mode(self, input: str, context):
    if any(kw in input.lower() for kw in ['urgent', 'asap']):
        return TurnMode.AGENTIC
    return TurnMode.SINGLE
```

### Pattern 2: Progressive Extraction
```python
if not context.basic_info:
    return "extract_basic"
elif not context.detailed_info:
    return "extract_detailed"
else:
    return "process"
```

### Pattern 3: Cache-First
```python
if context.cached_result:
    return context.cached_result  # Skip LLM
# Otherwise call LLM
```

### Pattern 4: Context-Aware Prompts
```python
context_text = json.dumps(context.dict())
prompt = f"Previous context:\n{context_text}\n\nNew input: {input}"
```

## Troubleshooting

### Policy Enforcement Failures
```
Error: Model call limit reached (5)
```
- **Cause**: Exceeded max_model_calls per turn
- **Fix**: Increase policy limit or reduce LLM calls

### Context Not Loading
```
context_manager.context is None
```
- **Cause**: load_context() not called or context missing
- **Fix**: Ensure load_context() loads from storage before checks

### Message Building Issues
- **Problem**: Prompts getting too long
- **Solution**: Summarize context or use task-specific prompts

### Turn Execution Timeout
- **Problem**: Exceeds timeout_seconds
- **Solution**: Reduce message history, simplify prompts, or increase timeout

## Next Steps

1. Review `examples/invoice_agent/` for complete implementation
2. Create your first ADK agent following the template
3. Add tests for routing, context, and message building
4. Deploy via FastAPI `/api/agents/run` endpoint
5. Monitor execution metrics and refine policies

---

For questions or issues, see the test suite in `tests/test_adk_architecture.py`.
