"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.routes import health, agent, mcp, telegram

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup — never log secret values directly
    logger.info(f"Starting {settings.APP_NAME} [env={settings.APP_ENV}]")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"Auth mode: {settings.AUTH_MODE}")
    if settings.TELEGRAM_ENABLED:
        allowlist_set = bool(settings.TELEGRAM_ALLOWED_USER_IDS.strip())
        logger.info(f"Telegram enabled | allowlist set: {allowlist_set}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


def _get_cors_origins() -> list[str]:
    """Parse CORS_ALLOWED_ORIGINS from settings.

    Never falls back to '*' — defaults to localhost dev origins.
    """
    raw = settings.CORS_ALLOWED_ORIGINS.strip()
    if not raw:
        return ["http://localhost:3000", "http://localhost:8000"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _get_allowed_hosts() -> list[str]:
    """Parse ALLOWED_HOSTS and include local defaults for dev/testing."""
    raw = settings.ALLOWED_HOSTS.strip()
    hosts = [h.strip() for h in raw.split(",") if h.strip()] if raw else []
    defaults = ["localhost", "127.0.0.1", "testserver"]
    for host in defaults:
        if host not in hosts:
            hosts.append(host)
    return hosts


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    configure_logging()

    is_prod = settings.APP_ENV == "prod"

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Personal agent runtime compatible with agentic-cowork-hub",
        lifespan=lifespan,
        # Disable interactive docs in production
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    # CORS middleware — closed by default; never use wildcard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    # Host header enforcement from ALLOWED_HOSTS.
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=_get_allowed_hosts(),
    )

    # Register routes
    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(agent.router, prefix="/api/agents", tags=["agent"])
    app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp"])
    app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])

    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        response: dict = {
            "message": "Welcome to personal-agent-runtime",
            "health": "/api/health/health",
        }
        if not is_prod:
            response["docs"] = "/docs"
        return response

    return app


# Create app instance
app = create_app()
