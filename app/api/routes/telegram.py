"""Telegram endpoint."""

import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.integrations.telegram.bot import get_telegram_bot
from app.integrations.telegram.handlers import TelegramHandler
from app.core.security import is_telegram_user_allowed, verify_telegram_signature
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TelegramWebhookUpdate(BaseModel):
    """Telegram webhook update."""

    update_id: int
    message: Optional[dict] = None


class TelegramMessageRequest(BaseModel):
    """Telegram message request."""

    chat_id: str
    text: str
    agent_id: str = "default"


@router.post("/webhook", tags=["telegram"])
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint.
    
    Args:
        request: Raw HTTP request
        
    Returns:
        Status
    """
    bot = get_telegram_bot()
    if not bot:
        raise HTTPException(status_code=400, detail="Telegram not configured")

    # Verify request signature before processing payload.
    signature = request.headers.get("X-Telegram-Signature")
    timestamp_header = request.headers.get("X-Telegram-Timestamp")
    if not signature or not timestamp_header:
        raise HTTPException(status_code=401, detail="Missing Telegram signature headers")

    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram timestamp") from exc

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram payload") from exc

    bot_token = bot.token
    if not verify_telegram_signature(
        token=bot_token,
        data=payload,
        signature=signature,
        timestamp=timestamp,
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram signature")

    update = TelegramWebhookUpdate.model_validate(payload)
    if not update.message:
        return {"ok": True}

    chat_id = str(update.message.get("chat", {}).get("id"))
    user_id = update.message.get("from", {}).get("id", 0)
    message_text = update.message.get("text", "")

    # ── Allowlist check ───────────────────────────────────────────────────────
    if not is_telegram_user_allowed(user_id):
        logger.warning(f"Telegram: rejected unauthorised user_id={user_id}")
        # Silently ignore — do not reveal allowlist existence to the caller
        return {"ok": True}

    if message_text.startswith("/"):
        # Handle command
        parts = message_text.split()
        command = parts[0][1:]
        args = parts[1:] if len(parts) > 1 else []
        handler = TelegramHandler()
        response = await handler.handle_command(chat_id, command, args)
    else:
        # Handle regular message
        handler = TelegramHandler()
        response = await handler.handle_message(chat_id, message_text)

    await bot.send_message(chat_id, response)
    return {"ok": True}


@router.post("/message", tags=["telegram"])
async def send_telegram_message(request: TelegramMessageRequest):
    """Send a message via Telegram.
    
    Args:
        request: Message request
        
    Returns:
        Status
    """
    bot = get_telegram_bot()
    if not bot:
        raise HTTPException(status_code=400, detail="Telegram not configured")

    success = await bot.send_message(request.chat_id, request.text)
    return {"success": success}


@router.get("/status", tags=["telegram"])
async def telegram_status():
    """Get Telegram bot status.
    
    Returns:
        Status information
    """
    bot = get_telegram_bot()
    if not bot:
        return {"enabled": False}

    return {
        "enabled": True,
        "is_running": bot.is_running,
        "bot_name": bot.base_url.split("/")[-1],
    }
