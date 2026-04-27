"""API dependencies."""

from typing import AsyncGenerator
from app.core.config import get_settings
from app.db import DatabaseSession


async def get_database() -> AsyncGenerator[DatabaseSession, None]:
    """Get database session dependency."""
    db = DatabaseSession(database_url=get_settings().DATABASE_URL)
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()
