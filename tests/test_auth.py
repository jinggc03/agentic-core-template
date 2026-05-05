"""Tests for canonical AUTH_MODE authentication."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.auth.context import AuthContext
from app.auth.dependencies import get_auth_context
from app.core.config import Settings


def _request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": raw_headers,
        }
    )


def _token(secret: str, *, sub: str = "user-1", expires_delta: timedelta | None = None) -> str:
    exp = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=5))
    return jwt.encode({"sub": sub, "exp": exp, "aud": "authenticated"}, secret, algorithm="HS256")


def test_auth_mode_off_returns_anonymous_context(monkeypatch):
    monkeypatch.setattr("app.core.config.settings", Settings(AUTH_MODE="off"))

    context = get_auth_context(_request())

    assert context == AuthContext(auth_mode="off")


def test_auth_context_lists_are_not_shared():
    first = AuthContext(auth_mode="off")
    second = AuthContext(auth_mode="off")

    first.roles.append("admin")
    first.scopes.append("agents:run")

    assert second.roles == []
    assert second.scopes == []
    assert first.tenant_id is None


def test_auth_mode_api_key_accepts_valid_key(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="api_key", API_KEY="secret"),
    )

    context = get_auth_context(_request({"X-API-Key": "secret"}))

    assert context.actor_id == "api_key"
    assert context.auth_mode == "api_key"


def test_auth_mode_api_key_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="api_key", API_KEY="secret"),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request())

    assert exc.value.status_code == 403


def test_auth_mode_api_key_rejects_invalid_key(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="api_key", API_KEY="secret"),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request({"X-API-Key": "wrong"}))

    assert exc.value.status_code == 403


def test_auth_mode_api_key_requires_configured_key(monkeypatch):
    monkeypatch.setattr("app.core.config.settings", Settings(AUTH_MODE="api_key", API_KEY=""))

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request({"X-API-Key": "secret"}))

    assert exc.value.status_code == 503


def test_auth_mode_supabase_accepts_valid_jwt(monkeypatch):
    secret = "supabase-secret"
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="supabase_auth", SUPABASE_JWT_SECRET=secret),
    )

    context = get_auth_context(_request({"Authorization": f"Bearer {_token(secret)}"}))

    assert context.actor_id == "user-1"
    assert context.auth_mode == "supabase_auth"
    assert context.tenant_id is None
    assert context.roles == []
    assert context.scopes == []


def test_auth_mode_supabase_rejects_missing_token(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="supabase_auth", SUPABASE_JWT_SECRET="secret"),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request())

    assert exc.value.status_code == 401


def test_auth_mode_supabase_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="supabase_auth", SUPABASE_JWT_SECRET="secret"),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request({"Authorization": "Bearer invalid-token"}))

    assert exc.value.status_code == 401


def test_auth_mode_supabase_rejects_expired_token(monkeypatch):
    secret = "supabase-secret"
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="supabase_auth", SUPABASE_JWT_SECRET=secret),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(
            _request(
                {
                    "Authorization": (
                        f"Bearer {_token(secret, expires_delta=timedelta(minutes=-1))}"
                    )
                }
            )
        )

    assert exc.value.status_code == 401


def test_auth_mode_supabase_requires_jwt_secret(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(AUTH_MODE="supabase_auth", SUPABASE_JWT_SECRET=""),
    )

    with pytest.raises(HTTPException) as exc:
        get_auth_context(_request({"Authorization": f"Bearer {_token('secret')}"}))

    assert exc.value.status_code == 503


def test_auth_mode_off_fails_environment_validation_in_prod():
    settings = Settings(
        APP_ENV="prd",
        AUTH_MODE="off",
        LLM_API_KEY="llm-key",
        SECRET_KEY="prod-secret",
    )

    errors = settings.validate_for_environment()

    assert settings.APP_ENV == "prod"
    assert any("AUTH_MODE=off is not allowed" in error for error in errors)


def test_auth_mode_supabase_prod_does_not_require_api_key():
    settings = Settings(
        APP_ENV="prod",
        AUTH_MODE="supabase_auth",
        API_KEY_ENABLED=True,
        API_KEY="",
        SUPABASE_JWT_SECRET="jwt-secret",
        LLM_API_KEY="llm-key",
        SECRET_KEY="prod-secret",
    )

    errors = settings.validate_for_environment()

    assert not any("API_KEY" in error for error in errors)
