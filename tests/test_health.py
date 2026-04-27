"""Test health endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_app_info(client):
    """Test app info endpoint."""
    response = client.get("/api/health/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "personal-agent-runtime"
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
