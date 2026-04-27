"""Health check endpoint."""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/info", tags=["health"])
async def app_info():
    """Application info endpoint.
    
    Returns:
        Application information
    """
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "debug": settings.APP_DEBUG,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
    }
