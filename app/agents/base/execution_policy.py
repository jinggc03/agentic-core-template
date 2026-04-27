"""Execution policy configuration and enforcement."""

from typing import Optional
from app.agents.base.types import ExecutionPolicy, ToolScope


def _settings_policy() -> ExecutionPolicy:
    """Build ExecutionPolicy from app settings (if available)."""
    try:
        from app.core.config import settings
        return ExecutionPolicy(
            max_model_calls=settings.MAX_MODEL_CALLS_PER_TURN,
            max_tool_calls=settings.MAX_TOOL_CALLS_PER_TURN,
            tool_scope=ToolScope.FULL,
            turn_limit=settings.MAX_AGENT_TURNS,
            timeout_seconds=settings.AGENT_TIMEOUT_SECONDS,
        )
    except Exception:
        pass
    # Fall back to safe defaults if settings unavailable
    return ExecutionPolicy(
        max_model_calls=1,
        max_tool_calls=5,
        tool_scope=ToolScope.FULL,
        turn_limit=10,
        timeout_seconds=60,
    )


# Default policies for different environments
DEFAULT_DEV_POLICY = ExecutionPolicy(
    max_model_calls=10,
    max_tool_calls=20,
    tool_scope=ToolScope.FULL,
    turn_limit=1000,
    timeout_seconds=60,
)

DEFAULT_PROD_POLICY = ExecutionPolicy(
    max_model_calls=5,
    max_tool_calls=10,
    tool_scope=ToolScope.INTERNAL,
    turn_limit=100,
    timeout_seconds=30,
)


def get_default_policy(environment: str = "dev") -> ExecutionPolicy:
    """Get default policy for environment.

    Reads limits from app settings when available, so that
    MAX_MODEL_CALLS_PER_TURN etc. in .env files are honoured.
    
    Args:
        environment: Environment name (dev/pre/prod)
        
    Returns:
        ExecutionPolicy instance
    """
    # If settings are accessible, derive from them
    try:
        from app.core.config import settings
        base = ExecutionPolicy(
            max_model_calls=settings.MAX_MODEL_CALLS_PER_TURN,
            max_tool_calls=settings.MAX_TOOL_CALLS_PER_TURN,
            turn_limit=settings.MAX_AGENT_TURNS,
            timeout_seconds=settings.AGENT_TIMEOUT_SECONDS,
            tool_scope=ToolScope.FULL if environment == "dev" else ToolScope.INTERNAL,
        )
        return base
    except Exception:
        pass

    # Fallback: environment-static defaults
    if environment in ("prod", "production"):
        return DEFAULT_PROD_POLICY
    elif environment in ("pre", "staging"):
        return ExecutionPolicy(
            max_model_calls=7,
            max_tool_calls=15,
            tool_scope=ToolScope.INTERNAL,
            turn_limit=500,
            timeout_seconds=45,
        )
    else:
        return DEFAULT_DEV_POLICY


class PolicyEnforcer:
    """Enforces execution policies during agent runs."""
    
    def __init__(self, policy: ExecutionPolicy):
        """Initialize enforcer with policy.
        
        Args:
            policy: ExecutionPolicy to enforce
        """
        self.policy = policy
        self.model_calls = 0
        self.tool_calls = 0
        self.turn_count = 0

    def on_model_call(self) -> tuple[bool, Optional[str]]:
        """Called before each model call.
        
        Returns:
            (is_allowed, error_message_if_not)
        """
        if self.model_calls >= self.policy.max_model_calls:
            return (
                False,
                f"Model call limit reached ({self.policy.max_model_calls})",
            )
        self.model_calls += 1
        return True, None

    def on_tool_call(self) -> tuple[bool, Optional[str]]:
        """Called before each tool call.
        
        Returns:
            (is_allowed, error_message_if_not)
        """
        if self.policy.tool_scope == ToolScope.NONE:
            return False, "Tools are disabled"
        
        if self.tool_calls >= self.policy.max_tool_calls:
            return (
                False,
                f"Tool call limit reached ({self.policy.max_tool_calls})",
            )
        self.tool_calls += 1
        return True, None

    def on_turn_start(self) -> tuple[bool, Optional[str]]:
        """Called at start of each turn.
        
        Returns:
            (is_allowed, error_message_if_not)
        """
        if self.turn_count >= self.policy.turn_limit:
            return False, f"Turn limit reached ({self.policy.turn_limit})"
        
        self.turn_count += 1
        self.model_calls = 0
        self.tool_calls = 0
        return True, None

    def reset(self):
        """Reset counters for new conversation."""
        self.model_calls = 0
        self.tool_calls = 0
        self.turn_count = 0
