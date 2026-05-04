"""Repository provider factory."""

from typing import Any, Optional

from app.repositories.base import RepositoryBundle
from app.repositories.memory import create_memory_repository_bundle


class RepositoryConfigurationError(RuntimeError):
    """Raised when repository configuration cannot be satisfied."""


_repository_bundle: Optional[RepositoryBundle] = None


def _get_settings() -> Any:
    """Load settings lazily to keep repository selection independent at import time."""
    from app.core.config import settings

    return settings


def get_repository_bundle(settings: Any | None = None) -> RepositoryBundle:
    """Return the configured repository bundle.

    Supabase-backed repositories are introduced in a later card. Until then,
    disabled Supabase uses the in-memory implementation and enabled Supabase
    fails clearly instead of pretending persistence is wired.
    """
    global _repository_bundle

    if settings is None and _repository_bundle is not None:
        return _repository_bundle

    resolved_settings = settings or _get_settings()

    if not resolved_settings.SUPABASE_ENABLED:
        bundle = create_memory_repository_bundle()
        if settings is None:
            _repository_bundle = bundle
        return bundle

    raise RepositoryConfigurationError(
        "Supabase repositories are not implemented yet. Keep SUPABASE_ENABLED=false "
        "or implement SUPA-007 before selecting Supabase-backed repositories."
    )


def reset_repository_bundle() -> None:
    """Clear the cached repository bundle."""
    global _repository_bundle

    _repository_bundle = None
