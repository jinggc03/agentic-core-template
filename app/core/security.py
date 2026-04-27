"""Security utilities and API key enforcement."""

import hmac
import hashlib
from typing import Optional

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── API Key Auth ────────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> str:
    """FastAPI dependency — validates the X-API-Key header.

    Use as:
        @router.post("/run")
        async def run(request: ..., _: str = Depends(require_api_key)):

    The check is skipped when API_KEY_ENABLED=False (dev convenience).
    In production this should always be enabled.
    """
    from app.core.config import settings  # lazy import to avoid circular

    if not settings.API_KEY_ENABLED:
        return "disabled"

    expected = settings.API_KEY
    if not expected:
        # Misconfiguration: enabled but no key set → refuse all requests
        logger.warning("API_KEY_ENABLED=true but API_KEY is not set — denying request")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key authentication is not configured",
        )

    if not api_key or not hmac.compare_digest(expected, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )

    return api_key


# ─── Telegram allowlist ───────────────────────────────────────────────────────

def is_telegram_user_allowed(user_id: int) -> bool:
    """Return True if the Telegram user_id is on the allowlist.

    When TELEGRAM_ALLOWED_USER_IDS is empty, all users are allowed
    (permissive mode for private/solo bots).
    """
    from app.core.config import settings  # lazy import

    allowlist_raw = settings.TELEGRAM_ALLOWED_USER_IDS.strip()
    if not allowlist_raw:
        return True  # No allowlist — open to all

    allowed_ids: set[int] = set()
    for part in allowlist_raw.split(","):
        part = part.strip()
        if part.isdigit():
            allowed_ids.add(int(part))

    return user_id in allowed_ids


# ─── Safe logging ─────────────────────────────────────────────────────────────

_SENSITIVE_SUBSTRINGS = {
    "API_KEY",
    "BOT_TOKEN",
    "SERVICE_ROLE_KEY",
    "SECRET_KEY",
    "OPENAI",
    "OPENROUTER",
    "SUPABASE",
    "TOKEN",
    "PASSWORD",
    "SECRET",
}


def verify_telegram_signature(
    token: str, data: dict, signature: str, timestamp: int, tolerance_seconds: int = 300
) -> bool:
    """Verify Telegram incoming message signature."""
    import time

    if abs(time.time() - timestamp) > tolerance_seconds:
        return False

    check_string = "\n".join([f"{key}={data[key]}" for key in sorted(data)])
    secret_key = hashlib.sha256(token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_hash, signature)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hmac.compare_digest(hash_password(password), hashed)


def mask_secret(secret: str, show_chars: int = 8) -> str:
    """Mask a secret for safe logging/display.
    
    Args:
        secret: The secret to mask
        show_chars: Number of characters to show at start and end
        
    Returns:
        Masked secret (e.g., 'sk-abc1234...xyz7890')
    """
    if not secret or len(secret) <= show_chars * 2:
        return "***"
    
    start = secret[:show_chars]
    end = secret[-show_chars:]
    return f"{start}...{end}"


def safe_repr_settings(settings_dict: dict) -> dict:
    """Create a safe representation of settings for logging.
    
    Masks sensitive values so they don't appear in logs.
    
    Args:
        settings_dict: Settings dictionary
        
    Returns:
        Dictionary with masked sensitive values
    """
    sensitive_keys = {
        "API_KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "KEY",
    }
    
    safe_dict = {}
    for key, value in settings_dict.items():
        # Check if this looks like a sensitive key
        is_sensitive = any(
            sens_key in key.upper() for sens_key in sensitive_keys
        )
        
        if is_sensitive and isinstance(value, str) and value:
            safe_dict[key] = mask_secret(value)
        else:
            safe_dict[key] = value
    
    return safe_dict

