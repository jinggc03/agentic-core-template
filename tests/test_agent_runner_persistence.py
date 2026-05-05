"""Tests for optional AgentRunner persistence."""

import asyncio

from app.agents.base.configured_agent import ConfiguredAgent
from app.agents.base.runner import AgentRunner
from app.providers.base import BaseLLMProvider
from app.repositories import create_memory_repository_bundle


class DummyProvider(BaseLLMProvider):
    def __init__(self, response: str = "dummy response"):
        super().__init__(api_key="test", model="dummy")
        self.response = response

    async def generate(self, **_kwargs) -> str:
        return self.response

    async def generate_with_tools(self, **_kwargs):
        return {"content": self.response}


class FailingMessagesRepository:
    def add_message(self, _record):
        raise RuntimeError("storage unavailable")

    def list_messages(self, _conversation_id):
        return []


def test_agent_runner_persists_turns_when_repositories_are_injected():
    bundle = create_memory_repository_bundle()
    agent = ConfiguredAgent(
        agent_id="dummy-agent",
        name="Dummy",
        system_prompt="Reply briefly.",
        provider=DummyProvider("hello"),
        conversation_id="conv-1",
    )
    runner = AgentRunner(agent, repositories=bundle)

    result = asyncio.run(runner.run_turn("hi"))

    assert result.success is True
    assert bundle.conversations.get_conversation("conv-1") is not None
    assert [message.role for message in bundle.messages.list_messages("conv-1")] == [
        "user",
        "assistant",
    ]
    state = bundle.agent_states.get_state("dummy-agent", "conv-1")
    assert state is not None
    assert state.state["turn_count"] == 1


def test_agent_runner_persistence_failure_does_not_break_turn():
    bundle = create_memory_repository_bundle()
    object.__setattr__(bundle, "messages", FailingMessagesRepository())
    agent = ConfiguredAgent(
        agent_id="dummy-agent",
        name="Dummy",
        system_prompt="Reply briefly.",
        provider=DummyProvider("hello"),
        conversation_id="conv-1",
    )
    runner = AgentRunner(agent, repositories=bundle)

    result = asyncio.run(runner.run_turn("hi"))

    assert result.success is True
    assert result.output == "hello"
