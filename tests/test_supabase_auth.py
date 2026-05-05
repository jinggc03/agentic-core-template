"""Tests for optional Supabase Auth dependency."""

import asyncio

import pytest
from fastapi import HTTPException

from app.integrations.supabase import auth


class FakeAuth:
    def get_user(self, token):
        assert token == "valid-token"
        return {
            "id": "user-1",
            "email": "user@example.com",
            "user_metadata": {"name": "Test User"},
        }


class FakeClient:
    auth = FakeAuth()


def test_get_current_supabase_user_validates_bearer_token(monkeypatch):
    monkeypatch.setattr(auth, "get_supabase_anon_client", lambda: FakeClient())

    user = asyncio.run(auth.get_current_supabase_user("Bearer valid-token"))

    assert user.id == "user-1"
    assert user.email == "user@example.com"
    assert user.metadata == {"name": "Test User"}


def test_get_current_supabase_user_rejects_missing_bearer_token():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_current_supabase_user(None))

    assert exc.value.status_code == 401


def test_get_current_supabase_user_rejects_invalid_token(monkeypatch):
    class FailingAuth:
        def get_user(self, _token):
            raise RuntimeError("invalid")

    class FailingClient:
        auth = FailingAuth()

    monkeypatch.setattr(auth, "get_supabase_anon_client", lambda: FailingClient())

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_current_supabase_user("Bearer invalid-token"))

    assert exc.value.status_code == 401
