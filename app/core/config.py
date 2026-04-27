"""Application configuration management with layered environment support.

Configuration hierarchy (lower index = lower priority):
  1. params/base/params.yml       — shared non-secret defaults (versioned)
  2. params/{APP_ENV}/params.yml  — environment overrides (versioned)
  3. .env                         — secrets / private values (git-ignored)
  4. System environment variables — highest priority

Non-secret values (feature flags, limits, log levels, etc.) belong in params/.
Secrets (API keys, tokens, passwords, connection strings) belong in .env.
"""

import os
from typing import Literal, Optional
from pathlib import Path

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with layered params + .env support.

    Configuration priority (highest to lowest):
    1. System environment variables
    2. .env  (secrets / private overrides, git-ignored)
    3. params/{APP_ENV}/params.yml  (environment-specific non-secret values)
    4. params/base/params.yml  (shared defaults)

    Usage:
        APP_ENV=dev  → loads params/base then params/dev then .env
        APP_ENV=prod → loads params/base then params/prod then .env
    """

    # ═════════════════════════════════════════════════════════════════
    # Application Environment
    # ═════════════════════════════════════════════════════════════════

    APP_ENV: Literal["dev", "pre", "prod"] = Field(
        default="dev",
        description="Application environment",
    )
    APP_NAME: str = Field(
        default="personal-agent-runtime",
        description="Application name",
    )
    APP_DEBUG: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # ═════════════════════════════════════════════════════════════════
    # Server Configuration
    # ═════════════════════════════════════════════════════════════════

    HOST: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    PORT: int = Field(
        default=8000,
        description="Server port",
    )
    RELOAD: bool = Field(
        default=True,
        description="Enable auto-reload (dev only)",
    )

    # ═════════════════════════════════════════════════════════════════
    # LLM Provider Configuration
    # ═════════════════════════════════════════════════════════════════

    LLM_PROVIDER: Literal["openrouter", "openai"] = Field(
        default="openrouter",
        description="LLM provider",
    )
    LLM_MODEL: str = Field(
        default="meta-llama/llama-3.1-70b-instruct",
        description="LLM model identifier",
    )
    LLM_API_KEY: str = Field(
        default="",
        description="Generic LLM API key (if provider-specific not set)",
    )

    # Provider-specific keys
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key",
    )
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key",
    )

    # ═════════════════════════════════════════════════════════════════
    # Telegram Configuration (Optional)
    # ═════════════════════════════════════════════════════════════════

    TELEGRAM_ENABLED: bool = Field(
        default=False,
        description="Enable Telegram bot",
    )
    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        description="Telegram bot token",
    )
    TELEGRAM_ALLOWED_USER_IDS: str = Field(
        default="",
        description="Comma-separated list of allowed Telegram user IDs",
    )

    # ═════════════════════════════════════════════════════════════════
    # Supabase/Database Configuration (Optional)
    # ═════════════════════════════════════════════════════════════════

    SUPABASE_ENABLED: bool = Field(
        default=False,
        description="Enable Supabase integration",
    )
    SUPABASE_URL: str = Field(
        default="",
        description="Supabase project URL",
    )
    SUPABASE_ANON_KEY: str = Field(
        default="",
        description="Supabase anonymous key",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="",
        description="Supabase service role key",
    )
    SUPABASE_DB_URL: str = Field(
        default="",
        description="Supabase database connection string",
    )
    DATABASE_URL: str = Field(
        default="",
        description="Generic database URL",
    )

    # ═════════════════════════════════════════════════════════════════
    # MCP Configuration (Model Context Protocol)
    # ═════════════════════════════════════════════════════════════════

    MCP_ENABLED: bool = Field(
        default=False,
        description="Enable MCP server",
    )
    MCP_SERVER_NAME: str = Field(
        default="personal-agent-runtime",
        description="MCP server name",
    )

    # ═════════════════════════════════════════════════════════════════
    # Feature Flags
    # ═════════════════════════════════════════════════════════════════

    ALLOW_AGENT_REGISTRATION: bool = Field(
        default=True,
        description="Allow dynamic agent registration",
    )
    ENABLE_METRICS: bool = Field(
        default=False,
        description="Enable metrics collection",
    )
    ENABLE_STRUCTURED_LOGS: bool = Field(
        default=False,
        description="Use structured logging (JSON)",
    )
    LOG_FORMAT: Literal["standard", "json"] = Field(
        default="standard",
        description="Log format",
    )

    # ═════════════════════════════════════════════════════════════════
    # Security (Production)
    # ═════════════════════════════════════════════════════════════════

    SECRET_KEY: str = Field(
        default="dev-insecure-key",
        description="Secret key for signing (production must override)",
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts",
    )

    # API key protection for sensitive endpoints
    API_KEY: str = Field(
        default="",
        description="API key required on protected endpoints (set to enable)",
    )
    API_KEY_ENABLED: bool = Field(
        default=False,
        description="Enforce X-API-Key header on POST /api/agents/* and POST /api/mcp/*",
    )

    # CORS — never use wildcard in prod
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins",
    )

    # ═════════════════════════════════════════════════════════════════
    # Execution Limits (applied to ADK ConfiguredAgent / AgentRunner)
    # ═════════════════════════════════════════════════════════════════

    MAX_MODEL_CALLS_PER_TURN: int = Field(
        default=1,
        description="Maximum LLM calls allowed per agent turn",
    )
    MAX_TOOL_CALLS_PER_TURN: int = Field(
        default=5,
        description="Maximum tool calls allowed per agent turn",
    )
    MAX_AGENT_TURNS: int = Field(
        default=10,
        description="Maximum conversation turns per agent session",
    )
    MAX_INPUT_CHARS: int = Field(
        default=8000,
        description="Maximum characters allowed in a single user input",
    )
    MAX_OUTPUT_CHARS: int = Field(
        default=12000,
        description="Maximum characters allowed in a single agent output",
    )
    AGENT_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Agent turn execution timeout in seconds",
    )

    # ═════════════════════════════════════════════════════════════════
    # Validation Rules
    # ═════════════════════════════════════════════════════════════════

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate and normalize APP_ENV."""
        if isinstance(v, str):
            v = v.lower().strip()
        return v or "dev"

    @field_validator("LLM_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", mode="before")
    @classmethod
    def validate_api_keys(cls, v: str) -> str:
        """Normalize API keys."""
        if v:
            return v.strip()
        return ""

    def validate_for_environment(self) -> list[str]:
        """Validate configuration based on environment.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Production validation - strict
        if self.APP_ENV == "prod":
            if self.APP_DEBUG:
                errors.append("APP_DEBUG must be False in production")

            if not self.LLM_API_KEY and not self.OPENROUTER_API_KEY and not self.OPENAI_API_KEY:
                errors.append("LLM API key required in production")

            if not self.SECRET_KEY or self.SECRET_KEY == "dev-insecure-key":
                errors.append("SECRET_KEY must be set in production")

            if self.API_KEY_ENABLED and not self.API_KEY:
                errors.append("API_KEY must be set when API_KEY_ENABLED=true in production")

            if self.SUPABASE_ENABLED:
                if not self.SUPABASE_URL:
                    errors.append("SUPABASE_URL required if SUPABASE_ENABLED")
                if not self.SUPABASE_ANON_KEY:
                    errors.append("SUPABASE_ANON_KEY required if SUPABASE_ENABLED")

        # Pre-production validation - semi-strict
        elif self.APP_ENV == "pre":
            if not self.LLM_API_KEY and not self.OPENROUTER_API_KEY and not self.OPENAI_API_KEY:
                errors.append("LLM API key strongly recommended in pre-production")

        # Dev validation - flexible
        else:
            if self.RELOAD is False and self.APP_ENV == "dev":
                # Just a warning, not an error
                pass

        return errors

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @classmethod
    def load_layered(cls) -> "Settings":
        """Load settings from layered params YAML files and .env secrets.

        Loading order (highest priority last):
          1. params/base/params.yml       — shared non-secret defaults
          2. params/{APP_ENV}/params.yml  — environment overrides
          3. .env                         — secrets / private overrides
          4. System environment variables — highest priority

        The YAML merge is deep: nested dicts are merged key-by-key so a
        per-environment file only needs to specify values that differ from base.

        Returns:
            Configured Settings instance
        """
        import yaml
        from dotenv import dotenv_values

        # Determine APP_ENV (system env takes precedence even at this stage)
        app_env = os.getenv("APP_ENV", "dev").lower()

        repo_root = Path(__file__).parent.parent.parent

        # ── 1-2. Load and deep-merge YAML params files ────────────────────────
        def _deep_merge(base: dict, override: dict) -> dict:
            """Recursively merge *override* into a copy of *base*."""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = _deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        def _load_yaml(path: Path) -> dict:
            if path.exists():
                with path.open("r") as f:
                    return yaml.safe_load(f) or {}
            return {}

        params_base = _load_yaml(repo_root / "params" / "base" / "params.yml")
        params_env  = _load_yaml(repo_root / "params" / app_env / "params.yml")
        yaml_merged = _deep_merge(params_base, params_env)

        # ── Flatten nested YAML → flat Settings field names ──────────────────
        # Map YAML structure to Settings field names (UPPER_SNAKE_CASE).
        def _flatten_yaml(data: dict) -> dict:
            flat: dict = {}

            app = data.get("app", {})
            if "env"        in app: flat["APP_ENV"]                = str(app["env"])
            if "name"       in app: flat["APP_NAME"]               = str(app["name"])
            if "debug"      in app: flat["APP_DEBUG"]              = app["debug"]
            if "log_level"  in app: flat["LOG_LEVEL"]              = str(app["log_level"])
            if "log_format" in app: flat["LOG_FORMAT"]             = str(app["log_format"])

            server = data.get("server", {})
            if "host"   in server: flat["HOST"]   = str(server["host"])
            if "port"   in server: flat["PORT"]   = int(server["port"])
            if "reload" in server: flat["RELOAD"] = server["reload"]

            llm = data.get("llm", {})
            if "provider" in llm: flat["LLM_PROVIDER"] = str(llm["provider"])
            if "model"    in llm: flat["LLM_MODEL"]    = str(llm["model"])

            sec = data.get("security", {})
            if "api_key_enabled"    in sec: flat["API_KEY_ENABLED"]      = sec["api_key_enabled"]
            if "cors_allowed_origins" in sec: flat["CORS_ALLOWED_ORIGINS"] = str(sec["cors_allowed_origins"])
            if "allowed_hosts"      in sec: flat["ALLOWED_HOSTS"]        = str(sec["allowed_hosts"])

            integ = data.get("integrations", {})
            tg = integ.get("telegram", {})
            if "enabled" in tg: flat["TELEGRAM_ENABLED"] = tg["enabled"]

            sb = integ.get("supabase", {})
            if "enabled" in sb: flat["SUPABASE_ENABLED"] = sb["enabled"]

            mcp = integ.get("mcp", {})
            if "enabled"     in mcp: flat["MCP_ENABLED"]     = mcp["enabled"]
            if "server_name" in mcp: flat["MCP_SERVER_NAME"] = str(mcp["server_name"])

            feat = data.get("features", {})
            if "allow_agent_registration" in feat: flat["ALLOW_AGENT_REGISTRATION"] = feat["allow_agent_registration"]
            if "enable_metrics"           in feat: flat["ENABLE_METRICS"]            = feat["enable_metrics"]
            if "enable_structured_logs"   in feat: flat["ENABLE_STRUCTURED_LOGS"]    = feat["enable_structured_logs"]

            lim = data.get("limits", {})
            if "max_model_calls_per_turn" in lim: flat["MAX_MODEL_CALLS_PER_TURN"] = int(lim["max_model_calls_per_turn"])
            if "max_tool_calls_per_turn"  in lim: flat["MAX_TOOL_CALLS_PER_TURN"]  = int(lim["max_tool_calls_per_turn"])
            if "max_agent_turns"          in lim: flat["MAX_AGENT_TURNS"]          = int(lim["max_agent_turns"])
            if "max_input_chars"          in lim: flat["MAX_INPUT_CHARS"]          = int(lim["max_input_chars"])
            if "max_output_chars"         in lim: flat["MAX_OUTPUT_CHARS"]         = int(lim["max_output_chars"])
            if "agent_timeout_seconds"    in lim: flat["AGENT_TIMEOUT_SECONDS"]    = int(lim["agent_timeout_seconds"])

            return flat

        flat_yaml = _flatten_yaml(yaml_merged)

        # ── 3. Load .env secrets (overrides YAML, overridden by system env) ──
        dot_env = repo_root / ".env"
        env_secrets = dict(dotenv_values(str(dot_env))) if dot_env.exists() else {}

        # Merge: yaml < .env secrets
        merged: dict = {**flat_yaml, **env_secrets}

        # ── 4. System env vars override everything ────────────────────────────
        # pydantic-settings v2 gives constructor kwargs higher priority than
        # os.environ, so we must NOT pass values already present in os.environ.
        system_env_keys = set(os.environ.keys())
        filtered_merged = {k: v for k, v in merged.items() if k not in system_env_keys}

        return cls(**filtered_merged)


def get_settings() -> Settings:
    """Get application settings (cached singleton).
    
    Uses layered loading to build configuration from:
    - .env.base
    - .env.{APP_ENV}
    - .env.local
    - System environment variables
    """
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings.load_layered()
    return _settings_cache


def validate_settings(settings: Settings) -> tuple[bool, list[str]]:
    """Validate settings for the current environment.
    
    Args:
        settings: Settings instance to validate
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = settings.validate_for_environment()
    return len(errors) == 0, errors


# Global settings cache
_settings_cache: Optional[Settings] = None

# Initialize on module load
settings = get_settings()
