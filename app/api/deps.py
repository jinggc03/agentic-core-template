"""FastAPI dependency injections.

Central place for shared dependencies used across routers.
Import from here rather than from app.core.security directly.

Usage:
    from app.api.deps import get_auth_context
    from app.auth.context import AuthContext
    
    @router.post("/run")
    async def run(
        request: RunRequest,
        auth_context: AuthContext = Depends(get_auth_context),
    ):
        ...
"""

from app.auth.dependencies import get_auth_context
from app.core.security import require_api_key

__all__ = ["get_auth_context", "require_api_key"]
