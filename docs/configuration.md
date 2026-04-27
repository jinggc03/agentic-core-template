# Configuration Management

Personal Agent Runtime uses a **layered YAML + secrets** configuration system. Non-secret settings live in versioned `params/` files; secrets live in a single git-ignored `.env` file.

## Overview

Configuration is loaded in the following priority order (later sources override earlier ones):

1. **`params/base/params.yml`** - Non-secret defaults shared across all environments (versioned)
2. **`params/{APP_ENV}/params.yml`** - Environment-specific overrides (versioned)
3. **`.env`** - Secrets and private values (git-ignored)
4. **System environment variables** - Override everything (highest priority)

This approach ensures:
- ✅ Base configuration is versioned and auditable
- ✅ Per-environment overrides are clear and diff-friendly
- ✅ Secrets never enter version control
- ✅ CI/CD systems can inject secrets via environment variables
- ✅ Local development needs only a single `.env` file

## Configuration Layers

### `params/base/params.yml`
**Non-secret defaults** — versioned, applies to all environments

```yaml
app:
  name: personal-agent-runtime
  env: dev
  debug: false
  log_level: INFO

server:
  host: 0.0.0.0
  port: 8000
  reload: false

llm:
  provider: openrouter
  model: meta-llama/llama-3.1-70b-instruct

limits:
  max_agent_turns: 10
  max_model_calls_per_turn: 3
  max_tool_calls_per_turn: 5
  agent_timeout_seconds: 60
```

### `params/dev/params.yml`, `params/pre/params.yml`, `params/prod/params.yml`
**Environment-specific overrides** — versioned, only specify deltas from base

```yaml
# params/dev/params.yml - Development
app:
  debug: true
  log_level: DEBUG
limits:
  max_agent_turns: 1000

# params/pre/params.yml - Pre-production
app:
  debug: false
security:
  api_key_enabled: true
cors:
  allowed_origins: https://staging.example.com

# params/prod/params.yml - Production
app:
  debug: false
  log_level: WARNING
security:
  api_key_enabled: true
limits:
  agent_timeout_seconds: 30
```

### `.env`
**Secrets only** — git-ignored, never versioned

Use this for:
- API keys (OpenRouter, OpenAI, etc.)
- Bot tokens (Telegram)
- Database credentials
- Any value that must not appear in git history

```env
# .env (not versioned)
APP_ENV=dev
OPENROUTER_API_KEY=sk-or-v1-xxxxx
TELEGRAM_BOT_TOKEN=123456:ABCDEF
SUPABASE_URL=https://xxxxx.supabase.co
```

## Getting Started

### 1. Create Secrets File

```bash
cp .env.example .env
# Then fill in real values for your secrets
```

### 2. Set Environment

```bash
# Set in .env (for local dev)
APP_ENV=dev

# Or via system env for CI/CD
export APP_ENV=prod
```

### 3. Review and Customise Params

The `params/` files are already configured with sensible defaults. For local overrides beyond what `params/dev/params.yml` provides, use system environment variables.

## Configuration Validation

Run diagnostics to verify configuration:

```bash
make config-check
```

Output shows:
- ✅ Active environment
- ✅ Enabled features
- ✅ Configuration file status
- ✅ Validation results
- ⚠️ Missing required secrets (masked)

Example output:
```
──────────────────────────────────────────────────────────────────
  Environment
──────────────────────────────────────────────────────────────────
  APP_ENV:            dev
  APP_DEBUG:          true
  LOG_LEVEL:          DEBUG

──────────────────────────────────────────────────────────────────
  LLM Provider
──────────────────────────────────────────────────────────────────
  LLM_PROVIDER:       openrouter
  LLM_MODEL:          meta-llama/llama-3.1-70b-instruct
  API Key configured: sk-or-v1...xxxxx

──────────────────────────────────────────────────────────────────
  Validation
──────────────────────────────────────────────────────────────────
  ✅ Configuration is valid for environment: DEV
```

## Configuration Fields Reference

### Application Environment

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_ENV` | dev/pre/prod | dev | Environment (determines which .env files load) |
| `APP_NAME` | string | personal-agent-runtime | Application name |
| `APP_DEBUG` | bool | false | Enable debug mode |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | INFO | Logging verbosity |

### Server

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HOST` | string | 0.0.0.0 | Server bind address |
| `PORT` | int | 8000 | Server port |
| `RELOAD` | bool | true | Auto-reload on file changes (dev only) |

### LLM Provider

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | openrouter/openai | openrouter | Which LLM provider to use |
| `LLM_MODEL` | string | meta-llama/llama-3.1-70b-instruct | Model identifier |
| `OPENROUTER_API_KEY` | string | (empty) | OpenRouter API key |
| `OPENAI_API_KEY` | string | (empty) | OpenAI API key |

### Integrations (Optional)

#### Telegram

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM_ENABLED` | bool | false | Enable Telegram bot |
| `TELEGRAM_BOT_TOKEN` | string | (empty) | Bot token from @BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | string | (empty) | Comma-separated user IDs allowed to use bot |

#### Supabase/Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SUPABASE_ENABLED` | bool | false | Enable Supabase integration |
| `SUPABASE_URL` | string | (empty) | Supabase project URL |
| `SUPABASE_ANON_KEY` | string | (empty) | Supabase public key |
| `SUPABASE_SERVICE_ROLE_KEY` | string | (empty) | Supabase service role key |
| `DATABASE_URL` | string | (empty) | Generic database connection string |

### MCP (Model Context Protocol)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MCP_ENABLED` | bool | false | Enable MCP server for tool exposure |
| `MCP_SERVER_NAME` | string | personal-agent-runtime | MCP server identifier |

### Features

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALLOW_AGENT_REGISTRATION` | bool | true | Template placeholder; documented future scope, not enforced in runtime yet |
| `ENABLE_METRICS` | bool | false | Template placeholder; no metrics pipeline is wired yet |
| `ENABLE_STRUCTURED_LOGS` | bool | false | Output logs as JSON |

### Security (Production)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | dev-insecure-key | Signing key (must change in production) |
| `ALLOWED_HOSTS` | string | localhost,127.0.0.1 | Comma-separated allowed hosts |

## Environment-Specific Behavior

### Development (APP_ENV=dev)

- ✅ Debug enabled by default
- ✅ Auto-reload enabled
- ✅ Flexible secret requirements
- ✅ Verbose logging (DEBUG level)
- ✅ API keys optional (can use test mode)

### Pre-production (APP_ENV=pre)

- ✅ Debug disabled
- ✅ Auto-reload disabled
- ⚠️ API keys should be configured
- ✅ Standard logging (INFO level)
- ✅ Tests all integrations but with more flexibility than prod

### Production (APP_ENV=prod)

- ❌ Debug mode disabled (enforced)
- ❌ Auto-reload disabled (enforced)
- ❌ All API keys required
- ✅ Conservative logging (WARNING level)
- ✅ Secrets must come from environment variables
- ✅ Strict validation on startup

## Best Practices

### 1. Never Commit Secrets

```bash
# ❌ BAD - Never do this
git add .env.local
git add .env.prod

# ✅ GOOD - Use .env.local for secrets
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env.local

# ✅ Verify gitignore is correct
cat .gitignore | grep .env
```

### 2. Configuration Per Environment

```bash
# Development
APP_ENV=dev python -m app.main

# Staging
APP_ENV=pre python -m app.main

# Production (all secrets from env vars)
APP_ENV=prod \
  OPENROUTER_API_KEY=$SECRET_KEY \
  TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN \
  python -m app.main
```

### 3. CI/CD Integration

In GitHub Actions, GitLab CI, or similar:

```yaml
# Set environment
env:
  APP_ENV: prod

# Inject secrets
jobs:
  deploy:
    env:
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
```

### 4. Debugging Configuration

```bash
# Check what configuration is active
make config-check

# Check layering by examining which files exist
ls -la .env*

# Debug by setting verbose logging
APP_ENV=dev LOG_LEVEL=DEBUG python -m app.main
```

## Troubleshooting

### "API Key required but not configured"

**Problem:** Configuration validation fails for LLM API key

**Solution:** 
```bash
# Option 1: Add to .env.local
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" >> .env.local

# Option 2: Set in environment
export OPENROUTER_API_KEY=sk-or-v1-your-key
```

### "Configuration is valid for DEV" but API calls fail

**Problem:** Configuration says valid but runtime fails

**Solution:** 
```bash
# Check that actual secrets are in .env.local
cat .env.local | grep API_KEY

# Verify the secret is actual (not placeholder)
python -c "from app.core.config import settings; print(settings.OPENROUTER_API_KEY[:20])"
```

### Different settings between machines

**Problem:** Configuration works locally but not in CI/production

**Solution:**
1. Run `make config-check` on both machines
2. Verify `.env.base` values match
3. Check for `.env.local` overrides (local-only, not in CI)
4. Verify environment variables in CI are set correctly

## Advanced: Custom Validation

Add environment-specific validation in `app/core/config.py`:

```python
def validate_for_environment(self) -> list[str]:
    """Validate configuration based on environment."""
    errors = []
    
    if self.APP_ENV == "prod":
        if not self.SECRET_KEY or self.SECRET_KEY == "dev-insecure-key":
            errors.append("SECRET_KEY must be set in production")
    
    return errors
```

Then check in your application:

```python
from app.core.config import settings, validate_settings

is_valid, errors = validate_settings(settings)
if not is_valid:
    for error in errors:
        logger.error(f"Configuration error: {error}")
    raise RuntimeError("Invalid configuration")
```
