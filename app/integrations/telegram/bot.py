"""Telegram bot."""

from typing import Optional
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot for agent interaction."""

    def __init__(self, token: str):
        """Initialize Telegram bot.
        
        Args:
            token: Telegram bot token
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.is_running = False

    async def start_polling(self) -> None:
        """Start bot in polling mode (dev-friendly)."""
        logger.info("Telegram bot started (polling mode)")
        self.is_running = True

    async def stop_polling(self) -> None:
        """Stop polling."""
        self.is_running = False
        logger.info("Telegram bot stopped")

    async def send_message(self, chat_id: str, text: str) -> bool:
        """Send message to chat.
        
        Args:
            chat_id: Chat ID
            text: Message text
            
        Returns:
            True if successful
        """
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {"chat_id": chat_id, "text": text}
                async with session.post(url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def get_updates(self, offset: int = 0) -> list:
        """Get bot updates (simplified).
        
        Args:
            offset: Update offset
            
        Returns:
            List of updates
        """
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/getUpdates"
                payload = {"offset": offset, "timeout": 30}
                async with session.get(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result", [])
                    return []
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return []


def get_telegram_bot() -> Optional[TelegramBot]:
    """Get Telegram bot if configured."""
    if settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN:
        return TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    return None
