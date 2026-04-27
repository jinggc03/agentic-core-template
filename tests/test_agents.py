"""Test agent endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.agents.registry import get_registry
from app.agents.base import ConfiguredAgent


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_agent():
    """Register a sample agent for testing."""
    
    class SampleAgent(ConfiguredAgent):
        def __init__(self, **kwargs):
            super().__init__(
                agent_id="sample-agent",
                name="Sample Agent",
                system_prompt="You are a test agent.",
                **kwargs,
            )
    
    registry = get_registry()
    registry.register("sample-agent", SampleAgent)
    return SampleAgent


def test_list_agents(client):
    """Test listing agents endpoint."""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "count" in data


def test_get_agent_info(client):
    """Test get agent info endpoint."""
    response = client.get("/api/agents/test-agent")
    assert response.status_code == 200
    data = response.json()
    assert "agent_id" in data
    assert "name" in data
    assert "available" in data


def test_run_agent_with_body_agent_id(client):
    """Test POST /api/agents/run with canonical input payload."""

    class DummyRegistry:
        def instantiate(self, agent_id: str, **kwargs):
            provider = AsyncMock()
            provider.generate = AsyncMock(return_value="ok-from-body-route")
            return ConfiguredAgent(
                agent_id=agent_id,
                name="Dummy",
                system_prompt="You are helpful",
                provider=provider,
                conversation_id=kwargs.get("conversation_id"),
            )

    with patch("app.api.routes.agent.get_registry", return_value=DummyRegistry()):
        response = client.post(
            "/api/agents/run",
            json={"agent_id": "invoice-agent", "input": "hello"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "invoice-agent"
    assert data["output"] == "ok-from-body-route"
    assert data["status"] == "success"


def test_run_agent_with_path_agent_id(client):
    """Test POST /api/agents/{agent_id}/run with canonical input payload."""

    class DummyRegistry:
        def instantiate(self, agent_id: str, **kwargs):
            provider = AsyncMock()
            provider.generate = AsyncMock(return_value="ok-from-path-route")
            return ConfiguredAgent(
                agent_id=agent_id,
                name="Dummy",
                system_prompt="You are helpful",
                provider=provider,
                conversation_id=kwargs.get("conversation_id"),
            )

    with patch("app.api.routes.agent.get_registry", return_value=DummyRegistry()):
        response = client.post(
            "/api/agents/invoice-agent/run",
            json={"input": "hello"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "invoice-agent"
    assert data["output"] == "ok-from-path-route"
    assert data["status"] == "success"
