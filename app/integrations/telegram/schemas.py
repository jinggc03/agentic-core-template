"""Telegram schema definitions."""

from pydantic import BaseModel
from typing import Optional


class TelegramMessage(BaseModel):
    """Telegram incoming message."""

    chat_id: str
    user_id: str
    message_text: str
    message_id: int
    timestamp: int


class TelegramUpdate(BaseModel):
    """Telegram update."""

    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[dict] = None


class TelegramResponse(BaseModel):
    """Telegram response."""

    chat_id: str
    text: str
    reply_to_message_id: Optional[int] = None
