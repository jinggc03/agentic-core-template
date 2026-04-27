"""Integration tests for Telegram webhook endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def _webhook_payload(text: str = "hola", user_id: int = 123, chat_id: int = 456) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "text": text,
            "from": {"id": user_id},
            "chat": {"id": chat_id},
        },
    }


def _signature_headers() -> dict:
    return {
        "X-Telegram-Signature": "signed",
        "X-Telegram-Timestamp": "1700000000",
    }


def test_webhook_allowlist_blocks_user(client):
    """Webhook should ignore messages from disallowed users."""
    bot = AsyncMock()
    bot.token = "bot-token"

    with patch("app.api.routes.telegram.get_telegram_bot", return_value=bot):
        with patch("app.api.routes.telegram.verify_telegram_signature", return_value=True):
            with patch("app.api.routes.telegram.is_telegram_user_allowed", return_value=False):
                response = client.post(
                    "/api/telegram/webhook",
                    headers=_signature_headers(),
                    json=_webhook_payload(),
                )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    bot.send_message.assert_not_called()


def test_webhook_executes_agent_and_sends_response(client):
    """Webhook should run handler and send resulting message via bot."""
    bot = AsyncMock()
    bot.token = "bot-token"

    handler = AsyncMock()
    handler.handle_message = AsyncMock(return_value="respuesta agente")
    handler.handle_command = AsyncMock(return_value="command response")

    with patch("app.api.routes.telegram.get_telegram_bot", return_value=bot):
        with patch("app.api.routes.telegram.verify_telegram_signature", return_value=True):
            with patch("app.api.routes.telegram.is_telegram_user_allowed", return_value=True):
                with patch("app.api.routes.telegram.TelegramHandler", return_value=handler):
                    response = client.post(
                        "/api/telegram/webhook",
                        headers=_signature_headers(),
                        json=_webhook_payload(text="hola runtime", chat_id=999),
                    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    handler.handle_message.assert_awaited_once()
    bot.send_message.assert_awaited_once_with("999", "respuesta agente")


def test_webhook_signature_invalid_returns_403(client):
    """Webhook should reject invalid signatures."""
    bot = AsyncMock()
    bot.token = "bot-token"

    with patch("app.api.routes.telegram.get_telegram_bot", return_value=bot):
        with patch("app.api.routes.telegram.verify_telegram_signature", return_value=False):
            response = client.post(
                "/api/telegram/webhook",
                headers=_signature_headers(),
                json=_webhook_payload(),
            )

    assert response.status_code == 403


def test_webhook_agent_error_response_is_forwarded(client):
    """Webhook should still send handler error text returned by TelegramHandler."""
    bot = AsyncMock()
    bot.token = "bot-token"

    handler = AsyncMock()
    handler.handle_message = AsyncMock(return_value="Error: provider down")
    handler.handle_command = AsyncMock(return_value="command response")

    with patch("app.api.routes.telegram.get_telegram_bot", return_value=bot):
        with patch("app.api.routes.telegram.verify_telegram_signature", return_value=True):
            with patch("app.api.routes.telegram.is_telegram_user_allowed", return_value=True):
                with patch("app.api.routes.telegram.TelegramHandler", return_value=handler):
                    response = client.post(
                        "/api/telegram/webhook",
                        headers=_signature_headers(),
                        json=_webhook_payload(text="hola error", chat_id=777),
                    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    bot.send_message.assert_awaited_once_with("777", "Error: provider down")
