"""Tests for optional Supabase client factory."""

from unittest.mock import Mock

import pytest

from app.core.config import Settings
from app.integrations.supabase import client
from app.integrations.supabase.client import SupabaseConfigurationError


@pytest.fixture(autouse=True)
def reset_clients():
    client.reset_supabase_clients()
    yield
    client.reset_supabase_clients()


def _settings(**kwargs) -> Settings:
    defaults = {
        "SUPABASE_ENABLED": True,
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_ANON_KEY": "anon-key",
        "SUPABASE_SERVICE_ROLE_KEY": "service-key",
    }
    defaults.update(kwargs)
    return Settings(**defaults)


def test_disabled_mode_raises_clear_error(monkeypatch):
    """Supabase client access should fail loudly when the integration is disabled."""
    monkeypatch.setattr(
        client,
        "_get_settings",
        lambda: _settings(SUPABASE_ENABLED=False),
    )

    with pytest.raises(SupabaseConfigurationError, match="Supabase is disabled"):
        client.get_supabase_anon_client()


def test_missing_url_raises_clear_error(monkeypatch):
    """SUPABASE_URL is required for any Supabase client."""
    monkeypatch.setattr(client, "_get_settings", lambda: _settings(SUPABASE_URL=""))

    with pytest.raises(SupabaseConfigurationError, match="SUPABASE_URL is required"):
        client.get_supabase_anon_client()


def test_missing_anon_key_raises_clear_error(monkeypatch):
    """Anon client requires SUPABASE_ANON_KEY."""
    monkeypatch.setattr(client, "_get_settings", lambda: _settings(SUPABASE_ANON_KEY=""))

    with pytest.raises(SupabaseConfigurationError, match="SUPABASE_ANON_KEY is required"):
        client.get_supabase_anon_client()


def test_missing_service_key_raises_clear_error(monkeypatch):
    """Service client requires SUPABASE_SERVICE_ROLE_KEY."""
    monkeypatch.setattr(
        client,
        "_get_settings",
        lambda: _settings(SUPABASE_SERVICE_ROLE_KEY=""),
    )

    with pytest.raises(
        SupabaseConfigurationError,
        match="SUPABASE_SERVICE_ROLE_KEY is required",
    ):
        client.get_supabase_service_client()


def test_anon_client_creation_uses_anon_key(monkeypatch):
    """Anon client should be created with SUPABASE_URL and SUPABASE_ANON_KEY."""
    create_client = Mock(return_value=object())
    monkeypatch.setattr(client, "_get_settings", lambda: _settings())
    monkeypatch.setattr(client, "_load_create_client", lambda: create_client)

    result = client.get_supabase_anon_client()

    assert result is create_client.return_value
    create_client.assert_called_once_with("https://example.supabase.co", "anon-key")


def test_service_client_creation_uses_service_role_key(monkeypatch):
    """Service client should be created with the backend-only service role key."""
    create_client = Mock(return_value=object())
    monkeypatch.setattr(client, "_get_settings", lambda: _settings())
    monkeypatch.setattr(client, "_load_create_client", lambda: create_client)

    result = client.get_supabase_service_client()

    assert result is create_client.return_value
    create_client.assert_called_once_with("https://example.supabase.co", "service-key")


def test_clients_are_cached(monkeypatch):
    """Repeated client access should reuse the cached SDK client."""
    create_client = Mock(return_value=object())
    monkeypatch.setattr(client, "_get_settings", lambda: _settings())
    monkeypatch.setattr(client, "_load_create_client", lambda: create_client)

    first = client.get_supabase_anon_client()
    second = client.get_supabase_anon_client()

    assert first is second
    create_client.assert_called_once()


def test_reset_supabase_clients_clears_cache(monkeypatch):
    """reset_supabase_clients should force the next getter call to create a new client."""
    first_client = object()
    second_client = object()
    create_client = Mock(side_effect=[first_client, second_client])
    monkeypatch.setattr(client, "_get_settings", lambda: _settings())
    monkeypatch.setattr(client, "_load_create_client", lambda: create_client)

    assert client.get_supabase_anon_client() is first_client
    client.reset_supabase_clients()
    assert client.get_supabase_anon_client() is second_client
    assert create_client.call_count == 2


def test_missing_sdk_import_raises_clear_error(monkeypatch):
    """Missing Supabase SDK should produce install guidance."""
    monkeypatch.setattr(client, "_get_settings", lambda: _settings())

    def raise_missing_sdk():
        raise SupabaseConfigurationError("Supabase SDK is not installed. Install project dependencies.")

    monkeypatch.setattr(client, "_load_create_client", raise_missing_sdk)

    with pytest.raises(SupabaseConfigurationError, match="Supabase SDK is not installed"):
        client.get_supabase_anon_client()
