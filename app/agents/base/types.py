"""ADK type definitions and data structures."""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TurnMode(str, Enum):
    """Turn execution mode."""
    
    SINGLE = "single"  # Single LLM call
    AGENTIC = "agentic"  # Multi-step with tool use
    STREAMING = "streaming"  # Streaming response


class ToolScope(str, Enum):
    """Scope of available tools."""
    
    NONE = "none"  # No tools
    INTERNAL = "internal"  # Internal tools only
    FULL = "full"  # Full tool access


class Message(BaseModel):
    """A single message in conversation."""
    
    role: str = Field(..., description="Message role (user/assistant/system/tool)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Snapshot(BaseModel):
    """Agent state snapshot (context cache)."""
    
    agent_id: str = Field(..., description="Agent identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    turn_count: int = Field(default=0, description="Number of turns")
    messages: List[Message] = Field(default_factory=list, description="Message history")
    state: Dict[str, Any] = Field(default_factory=dict, description="Agent state")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionPolicy:
    """Policy for controlling agent execution."""
    
    def __init__(
        self,
        max_model_calls: int = 5,
        max_tool_calls: int = 10,
        tool_scope: ToolScope = ToolScope.FULL,
        turn_limit: int = 100,
        timeout_seconds: int = 30,
    ):
        """Initialize execution policy.
        
        Args:
            max_model_calls: Maximum LLM calls per turn
            max_tool_calls: Maximum tool calls per turn
            tool_scope: Which tools are available
            turn_limit: Maximum turns per conversation
            timeout_seconds: Execution timeout
        """
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls
        self.tool_scope = tool_scope
        self.turn_limit = turn_limit
        self.timeout_seconds = timeout_seconds

    def is_within_limits(
        self,
        model_calls: int,
        tool_calls: int,
        turn_count: int,
    ) -> tuple[bool, Optional[str]]:
        """Check if execution is within policy limits.
        
        Args:
            model_calls: Number of model calls in this turn
            tool_calls: Number of tool calls in this turn
            turn_count: Total turns so far
            
        Returns:
            (is_valid, error_message_if_invalid)
        """
        if model_calls > self.max_model_calls:
            return False, f"Model calls ({model_calls}) exceeds max ({self.max_model_calls})"
        
        if tool_calls > self.max_tool_calls:
            return False, f"Tool calls ({tool_calls}) exceeds max ({self.max_tool_calls})"
        
        if turn_count > self.turn_limit:
            return False, f"Turn count ({turn_count}) exceeds limit ({self.turn_limit})"
        
        return True, None


class TurnContext(BaseModel):
    """Context for a single agent turn."""
    
    agent_id: str = Field(..., description="Agent identifier")
    conversation_id: str = Field(..., description="Conversation ID")
    turn_count: int = Field(default=0, description="Current turn number")
    user_input: str = Field(..., description="User input for this turn")
    system_prompt: str = Field(..., description="System prompt")
    mode: TurnMode = Field(default=TurnMode.SINGLE, description="Execution mode")
    policy: Optional[ExecutionPolicy] = Field(None, description="Execution policy")
    snapshot: Optional[Snapshot] = Field(None, description="Current state snapshot")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Turn metadata")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TurnResult(BaseModel):
    """Result of a turn execution."""
    
    success: bool = Field(..., description="Whether turn succeeded")
    output: str = Field(..., description="Agent response")
    model_calls: int = Field(default=0, description="LLM calls made")
    tool_calls: int = Field(default=0, description="Tool calls made")
    execution_time_ms: float = Field(default=0, description="Execution time")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
