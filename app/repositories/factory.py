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

    Disabled Supabase uses in-memory repositories so the template remains
    clone-and-run friendly. Enabled Supabase selects the service-role repository
    implementation and still initializes lazily.
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

    from app.repositories.supabase import create_supabase_repository_bundle

    bundle = create_supabase_repository_bundle()
    if settings is None:
        _repository_bundle = bundle
    return bundle


def reset_repository_bundle() -> None:
    """Clear the cached repository bundle."""
    global _repository_bundle

    _repository_bundle = None
