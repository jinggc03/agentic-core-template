"""Lazy Supabase client factory.

Supabase is optional infrastructure for this template. Importing this module must
not require Supabase credentials or the Supabase SDK unless a client is requested.
"""

from typing import Any, Callable


class SupabaseConfigurationError(RuntimeError):
    """Raised when Supabase is requested but cannot be configured."""


_anon_client: Any | None = None
_service_client: Any | None = None


def _get_settings() -> Any:
    """Load settings lazily to keep this integration optional."""
    from app.core.config import settings

    return settings


def _load_create_client() -> Callable[[str, str], Any]:
    """Load Supabase SDK lazily so disabled projects do not need it at import time."""
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseConfigurationError(
            "Supabase SDK is not installed. Install project dependencies with "
            "`pip install -e .` or install `supabase>=2,<3`."
        ) from exc

    return create_client


def _require_supabase_enabled(settings: Any) -> None:
    if not settings.SUPABASE_ENABLED:
        raise SupabaseConfigurationError(
            "Supabase is disabled. Set SUPABASE_ENABLED=true in params or environment "
            "before requesting a Supabase client."
        )


def _require_setting(settings: Any, name: str) -> str:
    value = getattr(settings, name, "")
    if not isinstance(value, str) or not value.strip():
        raise SupabaseConfigurationError(
            f"{name} is required when SUPABASE_ENABLED=true and a Supabase client is requested."
        )
    return value.strip()


def get_supabase_anon_client() -> Any:
    """Return a cached Supabase client using the anon key.

    The anon client is intended for RLS-safe operations. Repository implementations
    should prefer this client unless backend-only service-role access is required.
    """
    global _anon_client

    if _anon_client is not None:
        return _anon_client

    settings = _get_settings()
    _require_supabase_enabled(settings)
    url = _require_setting(settings, "SUPABASE_URL")
    anon_key = _require_setting(settings, "SUPABASE_ANON_KEY")

    _anon_client = _load_create_client()(url, anon_key)
    return _anon_client


def get_supabase_service_client() -> Any:
    """Return a cached Supabase client using the backend-only service role key."""
    global _service_client

    if _service_client is not None:
        return _service_client

    settings = _get_settings()
    _require_supabase_enabled(settings)
    url = _require_setting(settings, "SUPABASE_URL")
    service_key = _require_setting(settings, "SUPABASE_SERVICE_ROLE_KEY")

    _service_client = _load_create_client()(url, service_key)
    return _service_client


def reset_supabase_clients() -> None:
    """Clear cached Supabase clients.

    This is primarily useful in tests when settings or mocked SDK functions change.
    """
    global _anon_client, _service_client

    _anon_client = None
    _service_client = None
