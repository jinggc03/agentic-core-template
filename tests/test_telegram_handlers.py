"""Tests for Telegram handler ADK async execution path."""

import asyncio
from unittest.mock import AsyncMock

from app.agents.base import ConfiguredAgent
from app.agents.base.execution_policy import ExecutionPolicy, PolicyEnforcer
from app.integrations.telegram.handlers import TelegramHandler


class DummyRegistry:
    """Minimal registry stub for Telegram handler tests."""

    def __init__(self, agent: ConfiguredAgent):
        self._agent = agent

    def instantiate(self, agent_id: str, **kwargs) -> ConfiguredAgent:
        return self._agent

    def list_available(self) -> list[str]:
        return [self._agent.agent_id]


def test_handle_message_uses_async_turn_execution():
    """Telegram handler should execute message through async run_turn path."""
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value="telegram-ok")

    agent = ConfiguredAgent(
        agent_id="invoice-agent",
        name="Invoice Agent",
        system_prompt="You are helpful",
        provider=provider,
    )

    handler = TelegramHandler()
    handler.agent_registry = DummyRegistry(agent)

    response = asyncio.run(handler.handle_message("chat-1", "hello", "invoice-agent"))

    assert response == "telegram-ok"
    assert agent.turn_count == 1
    assert len(agent.messages) == 2


def test_handle_message_returns_error_when_policy_blocks():
    """Telegram handler should surface policy failures from ADK run_turn."""
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value="unused")

    policy = ExecutionPolicy(max_model_calls=0)
    agent = ConfiguredAgent(
        agent_id="invoice-agent",
        name="Invoice Agent",
        system_prompt="You are helpful",
        provider=provider,
        policy_enforcer=PolicyEnforcer(policy),
    )

    handler = TelegramHandler()
    handler.agent_registry = DummyRegistry(agent)

    response = asyncio.run(handler.handle_message("chat-1", "hello", "invoice-agent"))

    assert response.startswith("Error:")
    assert "model call" in response.lower()
    provider.generate.assert_not_called()
