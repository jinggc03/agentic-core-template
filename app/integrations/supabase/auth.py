"""Optional Supabase Auth helpers for FastAPI routes."""

from typing import Any, Optional

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, Field

from app.integrations.supabase.client import get_supabase_anon_client


class SupabaseUser(BaseModel):
    """Authenticated Supabase user context."""

    id: str
    email: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupabaseAuthError(RuntimeError):
    """Raised when Supabase Auth validation fails outside FastAPI."""


async def get_current_supabase_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> SupabaseUser:
    """Validate a Bearer token through Supabase Auth and return user context."""
    token = _extract_bearer_token(authorization)
    try:
        response = get_supabase_anon_client().auth.get_user(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase authentication token.",
        ) from exc

    user = getattr(response, "user", None) or response
    user_id = _get_attr_or_key(user, "id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase authentication token.",
        )

    metadata = (
        _get_attr_or_key(user, "user_metadata")
        or _get_attr_or_key(user, "app_metadata")
        or {}
    )
    return SupabaseUser(
        id=str(user_id),
        email=_get_attr_or_key(user, "email"),
        metadata=metadata,
    )


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token.",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token.",
        )
    return token


def _get_attr_or_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)
