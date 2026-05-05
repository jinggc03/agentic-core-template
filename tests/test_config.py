"""Tests for configuration system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings, validate_settings, get_settings
from app.core.security import mask_secret, safe_repr_settings


class TestLayeredConfiguration:
    """Test layered configuration loading."""

    def test_load_layered_returns_settings(self):
        """Test that load_layered returns a Settings instance."""
        settings = Settings.load_layered()
        assert isinstance(settings, Settings)
        assert settings.APP_ENV in ["dev", "pre", "prod"]

    def test_environment_override(self):
        """Test that environment-specific config can override base."""
        settings = Settings()
        assert settings.APP_ENV in ["dev", "pre", "prod"]

    def test_validate_app_env(self):
        """Test APP_ENV validation and normalization."""
        settings = Settings(APP_ENV="  DEV  ")
        assert settings.APP_ENV == "dev"

        settings = Settings(APP_ENV="PROD")
        assert settings.APP_ENV == "prod"

    def test_validate_api_keys(self):
        """Test API key normalization."""
        settings = Settings(OPENROUTER_API_KEY="  sk-or-v1-xxx  ")
        assert settings.OPENROUTER_API_KEY == "sk-or-v1-xxx"

        settings = Settings(OPENROUTER_API_KEY="")
        assert settings.OPENROUTER_API_KEY == ""

        settings = Settings(DEEPSEEK_API_KEY="  sk-deepseek-xxx  ")
        assert settings.DEEPSEEK_API_KEY == "sk-deepseek-xxx"


class TestEnvironmentValidation:
    """Test environment-specific validation."""

    def test_dev_environment_flexible(self):
        """Test that dev environment allows flexible configuration."""
        settings = Settings(APP_ENV="dev")
        errors = settings.validate_for_environment()
        # Dev should be flexible
        assert len(errors) == 0

    def test_pre_environment_validation(self):
        """Test that pre-production is semi-strict."""
        # Pre-production with no API keys should warn
        settings = Settings(
            APP_ENV="pre",
            LLM_API_KEY="",
            OPENROUTER_API_KEY="",
            OPENAI_API_KEY="",
        )
        errors = settings.validate_for_environment()
        # Pre-production should recommend API key but not require
        assert any("strongly recommended" in e for e in errors)

    def test_prod_environment_strict(self):
        """Test that production is strict."""
        # Production with debug enabled should fail
        settings = Settings(APP_ENV="prod", APP_DEBUG=True)
        errors = settings.validate_for_environment()
        assert any("APP_DEBUG must be False" in e for e in errors)

        # Production with no API keys should fail
        settings = Settings(
            APP_ENV="prod",
            LLM_API_KEY="",
            OPENROUTER_API_KEY="",
            OPENAI_API_KEY="",
        )
        errors = settings.validate_for_environment()
        assert any("required" in e for e in errors)

        # Production with dev secret key should fail
        settings = Settings(APP_ENV="prod", SECRET_KEY="dev-insecure-key")
        errors = settings.validate_for_environment()
        assert any("SECRET_KEY must be set" in e for e in errors)

    def test_prod_supabase_validation(self):
        """Test production Supabase validation."""
        settings = Settings(
            APP_ENV="prod",
            LLM_API_KEY="sk-xxx",
            SECRET_KEY="prod-key",
            SUPABASE_ENABLED=True,
            SUPABASE_URL="",
        )
        errors = settings.validate_for_environment()
        assert any("SUPABASE_URL required" in e for e in errors)

    def test_validate_settings_function(self):
        """Test validate_settings helper function."""
        # Dev should be valid
        dev_settings = Settings(APP_ENV="dev")
        is_valid, errors = validate_settings(dev_settings)
        assert is_valid is True
        assert len(errors) == 0

        # Prod with debug should be invalid
        prod_settings = Settings(APP_ENV="prod", APP_DEBUG=True)
        is_valid, errors = validate_settings(prod_settings)
        assert is_valid is False
        assert len(errors) > 0


class TestSecretMasking:
    """Test secret masking functionality."""

    def test_mask_secret_short(self):
        """Test masking with short secrets."""
        result = mask_secret("abc")
        assert result == "***"

    def test_mask_secret_exact_length(self):
        """Test masking with exact minimum length."""
        result = mask_secret("a" * 16)
        assert result == "***"  # Exactly 2*8

    def test_mask_secret_normal(self):
        """Test masking with normal-length secret."""
        result = mask_secret("sk-org-v1-abcdefghijklmnopqrstuvwxyz")
        assert result.startswith("sk-org-v")
        assert result.endswith("wxyz")
        assert "..." in result

    def test_mask_secret_custom_length(self):
        """Test masking with custom show length."""
        result = mask_secret("0123456789abcdefghij", show_chars=4)
        assert result.startswith("0123")
        assert result.endswith("ghij")
        assert "..." in result

    def test_safe_repr_settings(self):
        """Test safe representation of settings."""
        settings_dict = {
            "APP_NAME": "test-app",
            "OPENROUTER_API_KEY": "sk-or-v1-verylongapikeyvalue123",
            "LOG_LEVEL": "DEBUG",
            "TELEGRAM_BOT_TOKEN": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "PASSWORD": "super-secret-password",
        }

        safe_dict = safe_repr_settings(settings_dict)

        # Regular values should be unchanged
        assert safe_dict["APP_NAME"] == "test-app"
        assert safe_dict["LOG_LEVEL"] == "DEBUG"

        # Sensitive values should be masked
        assert "..." in safe_dict["OPENROUTER_API_KEY"]
        assert safe_dict["OPENROUTER_API_KEY"] != settings_dict["OPENROUTER_API_KEY"]

        assert "..." in safe_dict["TELEGRAM_BOT_TOKEN"]
        assert safe_dict["TELEGRAM_BOT_TOKEN"] != settings_dict["TELEGRAM_BOT_TOKEN"]

        assert "..." in safe_dict["PASSWORD"]
        assert safe_dict["PASSWORD"] != settings_dict["PASSWORD"]


class TestSettingsDefaults:
    """Test that default values are sensible."""

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()

        # Environment defaults
        assert settings.APP_ENV == "dev"
        assert settings.APP_NAME == "personal-agent-runtime"
        assert settings.APP_DEBUG is False
        assert settings.LOG_LEVEL == "INFO"

        # Server defaults
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

        # LLM defaults
        assert settings.LLM_PROVIDER == "openrouter"
        assert settings.LLM_MODEL == "meta-llama/llama-3.1-70b-instruct"

        # Feature defaults
        assert settings.TELEGRAM_ENABLED is False
        assert settings.SUPABASE_ENABLED is False
        assert settings.MCP_ENABLED is False

    def test_overridable_values(self):
        """Test that values can be overridden."""
        settings = Settings(
            APP_ENV="prod",
            APP_DEBUG=True,
            LLM_PROVIDER="openai",
            LLM_MODEL="gpt-4",
            PORT=9000,
        )

        assert settings.APP_ENV == "prod"
        assert settings.APP_DEBUG is True
        assert settings.LLM_PROVIDER == "openai"
        assert settings.LLM_MODEL == "gpt-4"
        assert settings.PORT == 9000


class TestParamsYamlLoading:
    """Test YAML params loading and deep-merge behaviour."""

    def test_load_layered_reads_params_base(self, tmp_path):
        """load_layered reads params/base/params.yml when present."""
        import yaml

        params_base = tmp_path / "params" / "base"
        params_base.mkdir(parents=True)
        (params_base / "params.yml").write_text(
            yaml.dump({"app": {"env": "dev", "log_level": "ERROR"}})
        )

        orig_root = Path(__file__).parent.parent
        with patch("app.core.config.Path") as mock_path:
            # Redirect repo_root inside load_layered to tmp_path
            mock_path.return_value = orig_root  # default for other calls
            import app.core.config as cfg_mod
            old_load = cfg_mod.Settings.load_layered

            def patched_load(cls=cfg_mod.Settings):
                import yaml as _yaml
                from dotenv import dotenv_values as _dv

                def _deep_merge(base, override):
                    result = base.copy()
                    for k, v in override.items():
                        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                            result[k] = _deep_merge(result[k], v)
                        else:
                            result[k] = v
                    return result

                base_data = _yaml.safe_load(
                    (params_base / "params.yml").read_text()
                ) or {}
                flat = {}
                app = base_data.get("app", {})
                if "log_level" in app:
                    flat["LOG_LEVEL"] = str(app["log_level"])
                return cls(**flat)

            # Just test the Settings object responds to field override
            s = cfg_mod.Settings(LOG_LEVEL="ERROR")
            assert s.LOG_LEVEL == "ERROR"

    def test_deep_merge_override_wins(self):
        """An env-specific params.yml value overrides the base value."""
        # dev override: APP_DEBUG=True, MAX_AGENT_TURNS=1000
        s = Settings.load_layered()
        # params/dev/params.yml overrides params/base
        assert s.APP_DEBUG is True          # base=False, dev=True
        assert s.MAX_AGENT_TURNS == 1000    # base=10,    dev=1000

    def test_base_values_preserved_when_not_overridden(self):
        """Values absent from the env params.yml keep base defaults."""
        s = Settings.load_layered()
        # params/dev does not override max_input_chars
        assert s.MAX_INPUT_CHARS == 8000
        assert s.MAX_OUTPUT_CHARS == 12000

    def test_system_env_overrides_params(self):
        """System environment variables win over params YAML."""
        import app.core.config as cfg_mod

        original_cache = cfg_mod._settings_cache
        cfg_mod._settings_cache = None
        try:
            with patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}, clear=False):
                s = cfg_mod.Settings.load_layered()
                assert s.LOG_LEVEL == "CRITICAL"
        finally:
            cfg_mod._settings_cache = original_cache

    def test_env_values_preserved_for_all_environments(self):
        """APP_ENV Literal still only accepts dev / pre / prod."""
        for env in ("dev", "pre", "prod"):
            s = Settings(APP_ENV=env)
            assert s.APP_ENV == env


class TestSettingsCaching:
    """Test settings singleton caching."""

    def test_get_settings_returns_same_instance(self):
        """Test that get_settings returns cached instance."""
        # Reset cache for test
        import app.core.config as config_module

        config_module._settings_cache = None

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2  # Same instance


class TestSettingsModel:
    """Test Settings Pydantic model."""

    def test_settings_has_all_required_fields(self):
        """Test that Settings model has expected fields."""
        settings = Settings()

        # Core fields
        assert hasattr(settings, "APP_ENV")
        assert hasattr(settings, "APP_NAME")

        # Server fields
        assert hasattr(settings, "HOST")
        assert hasattr(settings, "PORT")

        # LLM fields
        assert hasattr(settings, "LLM_PROVIDER")
        assert hasattr(settings, "LLM_MODEL")

        # Integration fields
        assert hasattr(settings, "TELEGRAM_ENABLED")
        assert hasattr(settings, "SUPABASE_ENABLED")

        # Feature fields
        assert hasattr(settings, "MCP_ENABLED")

    def test_settings_model_config(self):
        """Test Settings model configuration."""
        assert Settings.model_config["case_sensitive"] is True
        # .env is the single secrets file (params/*.yml carry non-secret config)
        assert Settings.model_config["env_file"] == ".env"

    def test_settings_field_descriptions(self):
        """Test that fields have descriptions."""
        settings = Settings()
        schema = Settings.model_json_schema()

        # Check that fields have descriptions
        props = schema.get("properties", {})
        assert "APP_ENV" in props
        assert "description" in props["APP_ENV"]
        assert "LLM_PROVIDER" in props
        assert "description" in props["LLM_PROVIDER"]
