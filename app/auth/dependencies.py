"""Authentication dependencies for FastAPI routes."""

import hmac
from typing import Any, Optional

import jwt
from fastapi import HTTPException, Request, status

from app.auth.context import AuthContext


def get_auth_context(request: Request) -> AuthContext:
    """Resolve the current request authentication context."""
    from app.core.config import settings

    auth_mode = settings.AUTH_MODE
    if auth_mode == "off":
        return AuthContext(auth_mode="off")
    if auth_mode == "api_key":
        return _resolve_api_key_context(request, settings)
    if auth_mode == "supabase_auth":
        return _resolve_supabase_context(request, settings)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported AUTH_MODE: {auth_mode}",
    )


def require_api_key_compat(api_key: Optional[str]) -> str:
    """Backward-compatible API key checker used by legacy imports."""
    from app.core.config import settings

    # Legacy behavior: API_KEY_ENABLED=false means no auth.
    auth_mode = getattr(settings, "AUTH_MODE", "off")
    if not isinstance(auth_mode, str):
        auth_mode = "off"
    api_key_enabled = getattr(settings, "API_KEY_ENABLED", False)
    if auth_mode == "off" and not api_key_enabled:
        return "disabled"
    if auth_mode not in {"off", "api_key"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key authentication is not active for this AUTH_MODE",
        )
    _validate_api_key(api_key, settings.API_KEY)
    return api_key or ""


def _resolve_api_key_context(request: Request, settings: Any) -> AuthContext:
    api_key = request.headers.get("X-API-Key")
    _validate_api_key(api_key, settings.API_KEY)
    return AuthContext(actor_id="api_key", auth_mode="api_key")


def _resolve_supabase_context(request: Request, settings: Any) -> AuthContext:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    token = _extract_bearer_token(request.headers.get("Authorization"))
    try:
        claims = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"], "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase authentication token expired",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase authentication token",
        ) from exc

    actor_id = claims.get("sub")
    if not actor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase authentication token",
        )
    return AuthContext(actor_id=str(actor_id), auth_mode="supabase_auth")


def _validate_api_key(api_key: Optional[str], expected: str) -> None:
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key authentication is not configured",
        )
    if not api_key or not hmac.compare_digest(expected, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Supabase Bearer token",
        )
    return token
