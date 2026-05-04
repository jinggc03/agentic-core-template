#!/usr/bin/env python3
"""Configuration diagnostics - shows active configuration without exposing secrets."""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Change to repo root for imports to work correctly
import os
os.chdir(repo_root)

from app.core.config import settings, validate_settings
from app.core.security import mask_secret, safe_repr_settings


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def print_config_check():
    """Print configuration diagnostics."""
    print("\n╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Configuration Diagnostics" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    # Environment
    print_section("Environment")
    print(f"  APP_ENV:            {settings.APP_ENV}")
    print(f"  APP_NAME:           {settings.APP_NAME}")
    print(f"  APP_DEBUG:          {settings.APP_DEBUG}")
    print(f"  LOG_LEVEL:          {settings.LOG_LEVEL}")

    # Server
    print_section("Server")
    print(f"  HOST:               {settings.HOST}")
    print(f"  PORT:               {settings.PORT}")
    print(f"  RELOAD:             {settings.RELOAD}")

    # LLM Configuration
    print_section("LLM Provider")
    print(f"  LLM_PROVIDER:       {settings.LLM_PROVIDER}")
    print(f"  LLM_MODEL:          {settings.LLM_MODEL}")

    # Check API keys (masked)
    llm_key = (
        settings.LLM_API_KEY
        or settings.OPENROUTER_API_KEY
        or settings.OPENAI_API_KEY
        or settings.DEEPSEEK_API_KEY
    )
    if llm_key:
        print(f"  API Key configured: {mask_secret(llm_key)}")
    else:
        print(f"  API Key configured: ⚠️  NOT SET")

    # Integrations
    print_section("Integrations")
    print(f"  Auth mode:          {settings.AUTH_MODE}")
    print(f"  Telegram enabled:   {settings.TELEGRAM_ENABLED}")
    if settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN:
        print(f"  Telegram token:     {mask_secret(settings.TELEGRAM_BOT_TOKEN)}")
    elif settings.TELEGRAM_ENABLED:
        print(f"  Telegram token:     ⚠️  NOT SET")

    print(f"  Supabase enabled:   {settings.SUPABASE_ENABLED}")
    if settings.SUPABASE_ENABLED:
        print(f"  Supabase URL:       {'✓ configured' if settings.SUPABASE_URL else '⚠️  NOT SET'}")
        print(f"  Supabase key:       {'✓ configured' if settings.SUPABASE_ANON_KEY else '⚠️  NOT SET'}")
    print(f"  RAG enabled:        {settings.RAG_ENABLED}")
    if settings.RAG_ENABLED:
        print(f"  RAG backend:        {settings.RAG_BACKEND}")
        print(f"  Embedding provider: {settings.EMBEDDING_PROVIDER}")
        embedding_key = settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY
        print(f"  Embedding key:      {'✓ configured' if embedding_key else '⚠️  NOT SET'}")

    # Features
    print_section("Features")
    print(f"  MCP enabled:        {settings.MCP_ENABLED}")
    print(f"  Allow registration: {settings.ALLOW_AGENT_REGISTRATION}")
    print(f"  Metrics:            {settings.ENABLE_METRICS}")
    print(f"  Structured logs:    {settings.ENABLE_STRUCTURED_LOGS}")

    # Validation
    print_section("Validation")
    is_valid, errors = validate_settings(settings)

    if is_valid:
        print("  ✅ Configuration is valid for environment: " + settings.APP_ENV.upper())
    else:
        print(f"  ❌ Configuration errors for {settings.APP_ENV.upper()}:")
        for error in errors:
            print(f"     - {error}")

    # Configuration files
    print_section("Configuration Files")
    params_files = {
        "params/base/params.yml":              repo_root / "params" / "base" / "params.yml",
        f"params/{settings.APP_ENV}/params.yml": repo_root / "params" / settings.APP_ENV / "params.yml",
        ".env (secrets)":                      repo_root / ".env",
    }

    for name, path in params_files.items():
        status = "✓ exists" if path.exists() else "✗ missing"
        print(f"  {name:40} {status}")

    # Loading order
    print_section("Configuration Loading Order")
    print(f"  Current APP_ENV: {settings.APP_ENV}")
    print("  Configuration will be loaded in this order (later overrides earlier):")
    print("    1. params/base/params.yml          (non-secret defaults, versioned)")
    print(f"    2. params/{settings.APP_ENV}/params.yml        (env overrides, versioned)")
    print("    3. .env                            (secrets / private, git-ignored)")
    print("    4. System environment variables    (highest priority)")

    print("\n" + "═" * 70 + "\n")


if __name__ == "__main__":
    print_config_check()
