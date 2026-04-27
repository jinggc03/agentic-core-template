"""FastAPI dependency injections.

Central place for shared dependencies used across routers.
Import from here rather than from app.core.security directly.

Usage:
    from app.api.deps import require_api_key
    
    @router.post("/run")
    async def run(request: RunRequest, _: str = Depends(require_api_key)):
        ...
"""

from app.core.security import require_api_key

__all__ = ["require_api_key"]
