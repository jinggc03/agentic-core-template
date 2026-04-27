"""Tests for ADK-aligned architecture."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.base import (
    ConfiguredAgent,
    AgentRunner,
    TurnMode,
    ToolScope,
    TurnResult,
    ExecutionPolicy,
    PolicyEnforcer,
)
from app.agents.registry import get_registry
from app.agents.base_agent import BaseAgent
from examples.invoice_agent import InvoiceAgent


class TestExecutionPolicy:
    """Test execution policy enforcement."""

    def test_policy_creation(self):
        """Test policy creation with defaults."""
        policy = ExecutionPolicy()
        assert policy.max_model_calls == 5
        assert policy.max_tool_calls == 10
        assert policy.turn_limit == 100

    def test_policy_enforcer_model_calls(self):
        """Test enforcer tracks model calls."""
        policy = ExecutionPolicy(max_model_calls=2)
        enforcer = PolicyEnforcer(policy)
        
        # First call should succeed
        allowed, _ = enforcer.on_model_call()
        assert allowed is True
        
        # Second call should succeed
        allowed, _ = enforcer.on_model_call()
        assert allowed is True
        
        # Third call should fail
        allowed, error = enforcer.on_model_call()
        assert allowed is False
        assert "limit" in error.lower() or "exceeds" in error.lower()

    def test_policy_enforcer_turn_starts(self):
        """Test enforcer controls turn starts."""
        policy = ExecutionPolicy(turn_limit=2)
        enforcer = PolicyEnforcer(policy)
        
        # First turn
        allowed, _ = enforcer.on_turn_start()
        assert allowed is True
        
        # Second turn
        allowed, _ = enforcer.on_turn_start()
        assert allowed is True
        
        # Third turn should fail
        allowed, error = enforcer.on_turn_start()
        assert allowed is False
        assert "limit" in error.lower()

    def test_policy_tool_scope_enforcement(self):
        """Test tool scope enforcement."""
        # No tools
        policy = ExecutionPolicy(tool_scope=ToolScope.NONE)
        enforcer = PolicyEnforcer(policy)
        allowed, error = enforcer.on_tool_call()
        assert allowed is False
        assert "disabled" in error.lower()


class TestConfiguredAgent:
    """Test ConfiguredAgent (ADK core agent)."""

    def test_agent_creation(self):
        """Test agent creation."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.turn_count == 0

    def test_agent_snapshot(self):
        """Test agent snapshot saving."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        
        snapshot = agent.save_snapshot()
        assert snapshot.agent_id == "test-agent"
        assert snapshot.turn_count == 0

    def test_agent_reset(self):
        """Test agent reset."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        
        agent.turn_count = 5
        agent.reset()
        
        assert agent.turn_count == 0
        assert len(agent.messages) == 0

    def test_agent_prepare_turn(self):
        """Test turn preparation."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        
        context = agent.prepare_turn("Hello")
        assert context.agent_id == "test-agent"
        assert context.user_input == "Hello"
        assert context.turn_count == 0


class TestAgentRunner:
    """Test AgentRunner orchestration."""

    def test_runner_creation(self):
        """Test runner creation."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        runner = AgentRunner(agent)
        
        assert runner.agent == agent
        assert runner.running is False

    def test_runner_summary(self):
        """Test runner execution summary."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        runner = AgentRunner(agent)
        
        summary = runner.get_execution_summary()
        assert summary["turns"] == 0
        assert summary["successful_turns"] == 0

    def test_runner_reset(self):
        """Test runner reset."""
        agent = ConfiguredAgent(
            agent_id="test-agent",
            name="Test Agent",
            system_prompt="You are helpful",
        )
        runner = AgentRunner(agent)
        runner.running = True
        
        runner.reset()
        assert runner.running is False
        assert agent.turn_count == 0


class TestAgentRegistry:
    """Test agent registry and discovery."""

    def test_registry_registration(self):
        """Test agent registration."""
        registry = get_registry()
        available = registry.list_available()
        
        # Should have invoice-agent loaded
        assert "invoice-agent" in available

    def test_registry_instantiation(self):
        """Test agent instantiation."""
        registry = get_registry()
        agent = registry.instantiate("invoice-agent")
        
        assert isinstance(agent, ConfiguredAgent)
        assert agent.agent_id == "invoice-agent"

    def test_registry_instance_caching(self):
        """Test instance caching."""
        registry = get_registry()
        
        instance1 = registry.instantiate("invoice-agent", conversation_id="conv1")
        instance2 = registry.get_instance("invoice-agent")
        
        assert instance1 is instance2

    def test_registry_release_instance(self):
        """Test instance release."""
        registry = get_registry()
        
        registry.instantiate("invoice-agent", conversation_id="conv1")
        registry.release_instance("invoice-agent")
        
        instance = registry.get_instance("invoice-agent")
        assert instance is None


class TestInvoiceAgentADK:
    """Test invoice agent with ADK pattern."""

    def test_invoice_agent_creation(self):
        """Test invoice agent creation."""
        agent = InvoiceAgent()
        
        assert agent.agent_id == "invoice-agent"
        assert isinstance(agent, ConfiguredAgent)
        assert hasattr(agent, "router")
        assert hasattr(agent, "context_manager")
        assert hasattr(agent, "message_builder")

    def test_invoice_agent_has_adK_components(self):
        """Test invoice agent has all ADK components."""
        agent = InvoiceAgent()
        
        # Router
        assert agent.router is not None
        assert hasattr(agent.router, "resolve_mode")
        
        # Context manager
        assert agent.context_manager is not None
        assert hasattr(agent.context_manager, "should_call_llm_for_extraction")
        
        # Message builder
        assert agent.message_builder is not None
        assert hasattr(agent.message_builder, "build_extraction_prompt")

    def test_invoice_agent_context(self):
        """Test invoice agent context."""
        agent = InvoiceAgent()
        context = agent.get_context()
        
        assert isinstance(context, dict)
        assert "has_invoice_data" in context
        assert "is_validated" in context


class TestBackwardCompatibility:
    """Test backward compatibility with BaseAgent."""

    def test_base_agent_creation(self):
        """Test BaseAgent creation (compatibility)."""
        agent = BaseAgent(
            agent_id="compat-agent",
            name="Compatibility Agent",
            system_prompt="You are helpful",
        )
        
        assert agent.agent_id == "compat-agent"
        # Should inherit from ConfiguredAgent
        assert isinstance(agent, ConfiguredAgent)

    def test_base_agent_legacy_api(self):
        """Test BaseAgent legacy API."""
        agent = BaseAgent(
            agent_id="compat-agent",
            name="Compatibility Agent",
            system_prompt="You are helpful",
        )
        
        # Legacy methods should exist
        assert hasattr(agent, "reset_history")
        assert hasattr(agent, "get_history")
        
        # Should work
        agent.reset_history()
        history = agent.get_history()
        assert isinstance(history, list)


class TestTurnMode:
    """Test turn mode handling."""

    def test_turn_modes_defined(self):
        """Test turn modes are defined."""
        assert TurnMode.SINGLE.value == "single"
        assert TurnMode.AGENTIC.value == "agentic"
        assert TurnMode.STREAMING.value == "streaming"

    def test_tool_scopes_defined(self):
        """Test tool scopes are defined."""
        assert ToolScope.NONE.value == "none"
        assert ToolScope.INTERNAL.value == "internal"
        assert ToolScope.FULL.value == "full"


class TestConfiguredAgentRunTurn:
    """Real run_turn tests with mocked providers."""

    def test_run_turn_success_updates_history(self):
        """ConfiguredAgent stores user+assistant messages and returns output."""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="ok-response")

        agent = ConfiguredAgent(
            agent_id="run-turn-agent",
            name="Run Turn Agent",
            system_prompt="You are helpful",
            provider=provider,
        )

        result = asyncio.run(agent.run_turn("Hello ADK"))

        assert result.success is True
        assert result.output == "ok-response"
        assert agent.turn_count == 1
        assert len(agent.messages) == 2
        assert agent.messages[0].role == "user"
        assert agent.messages[1].role == "assistant"

    def test_run_turn_timeout_returns_error(self):
        """ConfiguredAgent returns failure on timeout."""

        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(0.05)
            return "late-response"

        provider = AsyncMock()
        provider.generate = slow_generate

        agent = ConfiguredAgent(
            agent_id="timeout-agent",
            name="Timeout Agent",
            system_prompt="You are helpful",
            provider=provider,
        )

        with patch(
            "app.agents.base.configured_agent._get_limits",
            return_value={
                "max_input_chars": 8000,
                "max_output_chars": 12000,
                "timeout_seconds": 0.001,
            },
        ):
            result = asyncio.run(agent.run_turn("Hello"))

        assert result.success is False
        assert "timed out" in (result.error or "").lower()

    def test_run_turn_loop_guard_blocks_repeated_input(self):
        """ConfiguredAgent rejects repeated identical input after threshold."""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="same-output")

        agent = ConfiguredAgent(
            agent_id="loop-agent",
            name="Loop Agent",
            system_prompt="You are helpful",
            provider=provider,
        )

        first = asyncio.run(agent.run_turn("repeat me"))
        second = asyncio.run(agent.run_turn("repeat me"))
        third = asyncio.run(agent.run_turn("repeat me"))

        assert first.success is True
        assert second.success is True
        assert third.success is False
        assert "loop" in (third.error or "").lower()

    def test_run_turn_policy_blocks_model_call(self):
        """ConfiguredAgent enforces max_model_calls policy."""
        policy = ExecutionPolicy(max_model_calls=0)
        enforcer = PolicyEnforcer(policy)
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="never-used")

        agent = ConfiguredAgent(
            agent_id="policy-agent",
            name="Policy Agent",
            system_prompt="You are helpful",
            provider=provider,
            policy_enforcer=enforcer,
        )

        result = asyncio.run(agent.run_turn("Hello"))

        assert result.success is False
        assert "model call" in (result.error or "").lower()
        provider.generate.assert_not_called()


class TestAgentRunnerRunTurn:
    """Real AgentRunner run_turn execution tests."""

    def test_runner_run_turn_executes_and_tracks_result(self):
        """AgentRunner executes async turn and stores summary data."""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="runner-output")

        agent = ConfiguredAgent(
            agent_id="runner-agent",
            name="Runner Agent",
            system_prompt="You are helpful",
            provider=provider,
        )
        runner = AgentRunner(agent)

        result = asyncio.run(runner.run_turn("Run via runner"))

        assert result.success is True
        assert result.output == "runner-output"
        assert runner.running is True
        assert len(runner.turn_results) == 1
        summary = runner.get_execution_summary()
        assert summary["turns"] == 1
        assert summary["successful_turns"] == 1


class TestInvoiceAgentRunTurn:
    """InvoiceAgent run_turn tests with provider mocking."""

    def test_invoice_run_turn_success(self):
        """InvoiceAgent run_turn returns provider output and updates history."""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="invoice-processed")

        with patch(
            "examples.invoice_agent.agent.get_llm_provider",
            return_value=provider,
        ):
            agent = InvoiceAgent()

        result = asyncio.run(agent.run_turn("Extract invoice for Acme"))

        assert result.success is True
        assert result.output == "invoice-processed"
        assert result.model_calls == 1
        assert agent.turn_count == 1
        assert len(agent.messages) == 2

    def test_invoice_run_turn_policy_block(self):
        """InvoiceAgent enforces execution policy before model call."""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value="unused")

        with patch(
            "examples.invoice_agent.agent.get_llm_provider",
            return_value=provider,
        ):
            agent = InvoiceAgent()

        agent.policy_enforcer.policy.max_model_calls = 0
        result = asyncio.run(agent.run_turn("Extract invoice for Acme"))

        assert result.success is False
        assert "model call" in (result.error or "").lower()
        provider.generate.assert_not_called()
