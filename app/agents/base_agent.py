"""Backward compatibility layer for BaseAgent.

This module provides a compatibility wrapper so existing code using BaseAgent
continues to work while we transition to ConfiguredAgent (ADK-aligned).
"""

import warnings
from typing import Optional, List, Dict
from app.agents.base import ConfiguredAgent
from app.providers.base import BaseLLMProvider
from app.providers.factory import get_llm_provider
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ConfiguredAgent):
    """Backward compatibility wrapper for BaseAgent.
    
    Extends ConfiguredAgent with simplified interface for quick prototyping.
    New code should use ConfiguredAgent directly.

    Deprecated:
        BaseAgent is kept for compatibility only and will be removed in a
        future major version.
    """

    def __init__(
        self,
        agent_id: str = "default",
        name: str = "Agent",
        system_prompt: str = "You are a helpful assistant.",
        provider: Optional[BaseLLMProvider] = None,
        model: str = "",
    ):
        """Initialize agent (legacy interface).
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            system_prompt: System prompt
            provider: LLM provider
            model: Optional model override
        """
        warnings.warn(
            "BaseAgent is deprecated, use ConfiguredAgent",
            DeprecationWarning,
            stacklevel=2,
        )

        super().__init__(
            agent_id=agent_id,
            name=name,
            system_prompt=system_prompt,
            provider=provider or get_llm_provider(),
        )
        
        if model and self.provider:
            self.provider.model = model

    def run(self, user_input: str) -> str:
        """Run agent (legacy interface).
        
        Args:
            user_input: User input
            
        Returns:
            Agent response
        """
        return super().run(user_input)

    def reset_history(self) -> None:
        """Reset message history (legacy API)."""
        self.reset()

    def get_history(self) -> List[Dict[str, str]]:
        """Get message history (legacy API).
        
        Returns:
            Message history as list of dicts
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self.agent_id}, "
            f"name={self.name})"
        )


__all__ = ["BaseAgent"]
