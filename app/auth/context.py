"""Authentication context shared across API, runtime, and services."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

AuthMode = Literal["off", "api_key", "supabase_auth", "telegram_webhook"]


class AuthContext(BaseModel):
    """Resolved authentication context.

    Tenant, roles, and scopes are intentionally future-ready. They are not
    populated from user-editable claims.
    """

    actor_id: Optional[str] = None
    auth_mode: AuthMode
    tenant_id: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
