"""Security guardrails tests.

Tests for:
- API key enforcement (authorized / unauthorized)
- Telegram allowlist
- Execution limits (input length, output truncation, timeout)
- Anti-loop protection (LoopGuard)
- CORS origins configuration
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.agents.base import ConfiguredAgent, LoopGuard, LoopDetectedError
from app.core.security import is_telegram_user_allowed, require_api_key


# ─── API Key enforcement ──────────────────────────────────────────────────────

class TestApiKeyEnforcement:
    """Test X-API-Key header enforcement on protected endpoints."""

    def test_key_check_valid(self):
        """Valid key passes require_api_key."""
        with patch("app.core.config.settings") as s:
            s.API_KEY_ENABLED = True
            s.API_KEY = "secret-key"
            result = require_api_key(api_key="secret-key")
            assert result == "secret-key"

    def test_key_check_invalid(self):
        """Wrong key raises 403."""
        from fastapi import HTTPException

        with patch("app.core.config.settings") as s:
            s.API_KEY_ENABLED = True
            s.API_KEY = "secret-key"
            with pytest.raises(HTTPException) as exc_info:
                require_api_key(api_key="wrong-key")
            assert exc_info.value.status_code == 403

    def test_key_check_missing(self):
        """Missing key raises 403."""
        from fastapi import HTTPException

        with patch("app.core.config.settings") as s:
            s.API_KEY_ENABLED = True
            s.API_KEY = "secret-key"
            with pytest.raises(HTTPException) as exc_info:
                require_api_key(api_key=None)
            assert exc_info.value.status_code == 403

    def test_no_key_when_disabled(self):
        """When API_KEY_ENABLED=False, endpoint accessible without key."""
        with patch("app.core.config.settings") as s:
            s.API_KEY_ENABLED = False
            s.API_KEY = ""
            result = require_api_key(api_key=None)
            assert result == "disabled"

    def test_503_when_key_enabled_but_not_set(self):
        """503 when API_KEY_ENABLED=true but API_KEY is empty."""
        from fastapi import HTTPException

        with patch("app.core.config.settings") as s:
            s.API_KEY_ENABLED = True
            s.API_KEY = ""
            with pytest.raises(HTTPException) as exc_info:
                require_api_key(api_key="any-value")
            assert exc_info.value.status_code == 503


# ─── Telegram allowlist ───────────────────────────────────────────────────────

class TestTelegramAllowlist:
    """Test Telegram user ID allowlist."""

    def test_empty_allowlist_allows_all(self):
        """Empty TELEGRAM_ALLOWED_USER_IDS allows everyone."""
        with patch("app.core.config.settings") as s:
            s.TELEGRAM_ALLOWED_USER_IDS = ""
            assert is_telegram_user_allowed(12345) is True
            assert is_telegram_user_allowed(99999) is True

    def test_allowlist_permits_listed_user(self):
        """User in allowlist is permitted."""
        with patch("app.core.config.settings") as s:
            s.TELEGRAM_ALLOWED_USER_IDS = "111, 222, 333"
            assert is_telegram_user_allowed(222) is True

    def test_allowlist_blocks_unlisted_user(self):
        """User not in allowlist is rejected."""
        with patch("app.core.config.settings") as s:
            s.TELEGRAM_ALLOWED_USER_IDS = "111,222"
            assert is_telegram_user_allowed(999) is False

    def test_allowlist_whitespace_handling(self):
        """Handles whitespace around IDs."""
        with patch("app.core.config.settings") as s:
            s.TELEGRAM_ALLOWED_USER_IDS = " 100 , 200 , 300 "
            assert is_telegram_user_allowed(200) is True
            assert is_telegram_user_allowed(400) is False


# ─── Execution limits ─────────────────────────────────────────────────────────

class TestExecutionLimits:
    """Test input/output length guards and timeout handling."""

    def _make_agent(self, max_input=8000, max_output=12000, timeout=60):
        """Create an agent with mock settings."""
        agent = ConfiguredAgent(
            agent_id="test",
            name="Test",
            system_prompt="You are helpful",
        )
        return agent

    def test_input_too_long_returns_error(self):
        """Input exceeding MAX_INPUT_CHARS returns TurnResult with error."""
        import asyncio

        agent = self._make_agent()

        long_input = "x" * 9000

        with patch(
            "app.agents.base.configured_agent._get_limits",
            return_value={"max_input_chars": 8000, "max_output_chars": 12000, "timeout_seconds": 60},
        ):
            result = asyncio.run(agent.run_turn(long_input))

        assert result.success is False
        assert "too long" in result.error.lower()

    def test_timeout_returns_error(self):
        """Execution exceeding timeout returns TurnResult with error."""
        import asyncio

        agent = ConfiguredAgent(
            agent_id="timeout-test",
            name="Test",
            system_prompt="You are helpful",
        )

        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(100)  # Never completes

        agent.provider = MagicMock()
        agent.provider.generate = slow_generate

        with patch(
            "app.agents.base.configured_agent._get_limits",
            return_value={"max_input_chars": 8000, "max_output_chars": 12000, "timeout_seconds": 0.1},
        ):
            result = asyncio.run(agent.run_turn("Hello"))

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_output_truncated_when_too_long(self):
        """Output longer than MAX_OUTPUT_CHARS is truncated."""
        import asyncio

        agent = ConfiguredAgent(
            agent_id="output-test",
            name="Test",
            system_prompt="You are helpful",
        )

        async def long_response(*args, **kwargs):
            return "y" * 15000

        agent.provider = MagicMock()
        agent.provider.generate = long_response

        with patch(
            "app.agents.base.configured_agent._get_limits",
            return_value={"max_input_chars": 8000, "max_output_chars": 100, "timeout_seconds": 60},
        ):
            result = asyncio.run(agent.run_turn("Hello"))

        assert result.success is True
        assert len(result.output) == 100


# ─── Anti-loop protection ─────────────────────────────────────────────────────

class TestLoopGuard:
    """Test LoopGuard detection patterns."""

    def test_repeated_input_triggers_error(self):
        """Same input 3+ times in a row raises LoopDetectedError."""
        guard = LoopGuard(max_repeated_input=3)

        guard.check_input("hello")
        guard.check_input("hello")
        with pytest.raises(LoopDetectedError) as exc_info:
            guard.check_input("hello")
        assert "loop" in str(exc_info.value).lower()

    def test_different_inputs_dont_trigger(self):
        """Different inputs reset the repeat counter."""
        guard = LoopGuard(max_repeated_input=3)

        guard.check_input("hello")
        guard.check_input("world")  # Different — resets count
        guard.check_input("hello")  # Repeat count restarted
        # Should not raise

    def test_same_tool_consecutive_triggers(self):
        """Same tool called too many consecutive times raises error."""
        guard = LoopGuard(max_same_tool_consecutive=3)

        guard.check_tool_call("search")
        guard.check_tool_call("search")
        with pytest.raises(LoopDetectedError):
            guard.check_tool_call("search")

    def test_different_tools_dont_trigger(self):
        """Different tools reset the consecutive counter."""
        guard = LoopGuard(max_same_tool_consecutive=3)

        guard.check_tool_call("search")
        guard.check_tool_call("fetch")  # Different tool
        guard.check_tool_call("search")  # Resets count

    def test_repeated_output_triggers_error(self):
        """Same output 3+ times raises LoopDetectedError."""
        guard = LoopGuard(max_repeated_output=3)

        guard.check_output("I cannot help with that.")
        guard.check_output("I cannot help with that.")
        with pytest.raises(LoopDetectedError):
            guard.check_output("I cannot help with that.")

    def test_reset_clears_counters(self):
        """reset() clears all counters."""
        guard = LoopGuard(max_repeated_input=3)

        guard.check_input("hello")
        guard.check_input("hello")
        guard.reset()

        # After reset, two more identical inputs should be fine
        guard.check_input("hello")
        guard.check_input("hello")
        # Does not raise on third because count reset to 1 at reset

    def test_loop_guard_integrated_in_agent(self):
        """ConfiguredAgent resets loop guard on agent.reset()."""
        agent = ConfiguredAgent(
            agent_id="loop-test",
            name="Test",
            system_prompt="You are helpful",
        )

        # Simulate two repeated checks
        agent.loop_guard.check_input("hello")
        agent.loop_guard.check_input("hello")

        agent.reset()

        # After agent reset, counters cleared
        assert agent.loop_guard._input_repeat_count == 0


# ─── CORS configuration ───────────────────────────────────────────────────────

class TestCORSConfiguration:
    """Test CORS is never wildcard."""

    def test_cors_origins_parsed(self):
        """CORS origins are parsed from settings."""
        from app.main import _get_cors_origins

        with patch("app.main.settings") as s:
            s.CORS_ALLOWED_ORIGINS = "http://localhost:3000,https://example.com"
            origins = _get_cors_origins()
            assert "http://localhost:3000" in origins
            assert "https://example.com" in origins
            assert "*" not in origins

    def test_cors_no_wildcard_on_empty(self):
        """Even with empty setting, no wildcard fallback."""
        from app.main import _get_cors_origins

        with patch("app.main.settings") as s:
            s.CORS_ALLOWED_ORIGINS = ""
            origins = _get_cors_origins()
            assert "*" not in origins
            # Falls back to localhost defaults
            assert len(origins) > 0


# ─── Safe logging / secret masking ───────────────────────────────────────────

class TestSafeLogging:
    """Test that sensitive keys are masked in logs."""

    def test_mask_secret_hides_middle(self):
        """mask_secret shows only start and end."""
        from app.core.security import mask_secret

        secret = "sk-abcdef1234567890xyz"
        masked = mask_secret(secret, show_chars=4)
        assert "sk-a" in masked
        assert "1234567890" not in masked  # middle hidden

    def test_safe_repr_masks_sensitive_keys(self):
        """safe_repr_settings masks known sensitive keys."""
        from app.core.security import safe_repr_settings

        raw = {
            "API_KEY": "real-secret",
            "OPENAI_API_KEY": "sk-real",
            "APP_NAME": "test-app",
            "PORT": 8000,
        }
        safe = safe_repr_settings(raw)
        assert "real-secret" not in str(safe)
        assert "sk-real" not in str(safe)
        assert safe["APP_NAME"] == "test-app"
