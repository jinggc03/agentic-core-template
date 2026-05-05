"""Integration tests for MCP tool calling endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_mcp_tool_call_requires_api_key_when_enabled(client):
    """POST /api/mcp/tools/call should enforce API key when enabled."""
    with patch("app.core.config.settings") as s:
        s.AUTH_MODE = "api_key"
        s.API_KEY_ENABLED = True
        s.API_KEY = "secret"

        response = client.post(
            "/api/mcp/tools/call",
            json={"tool_id": "echo", "arguments": {"value": 1}},
        )

    assert response.status_code == 403


def test_mcp_tool_call_input_parsing_validation(client):
    """Invalid payload should fail with 422 (missing required fields)."""
    response = client.post(
        "/api/mcp/tools/call",
        json={"arguments": {"value": 1}},
    )
    assert response.status_code == 422


def test_mcp_tool_call_response_format(client):
    """Endpoint should return tool response payload format."""

    class DummyMCPServer:
        async def handle_tool_call(self, tool_id, arguments):
            return {"result": {"tool_id": tool_id, "arguments": arguments}}

    with patch("app.api.routes.mcp.get_mcp_server", return_value=DummyMCPServer()):
        with patch("app.core.config.settings") as s:
            s.AUTH_MODE = "api_key"
            s.API_KEY_ENABLED = True
            s.API_KEY = "secret"

            response = client.post(
                "/api/mcp/tools/call",
                headers={"X-API-Key": "secret"},
                json={"tool_id": "echo", "arguments": {"value": 42}},
            )

    assert response.status_code == 200
    payload = response.json()
    assert "result" in payload
    assert payload["result"]["tool_id"] == "echo"
    assert payload["result"]["arguments"]["value"] == 42
