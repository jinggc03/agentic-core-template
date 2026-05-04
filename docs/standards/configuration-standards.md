# Configuration Standards

This repository uses a **params/ YAML + secrets** configuration system. Non-secret settings live in versioned `params/` files; secrets live in a single git-ignored `.env` file.

---

## File hierarchy

Files are loaded in order. Later sources take precedence over earlier ones.

```
params/base/params.yml       ← versioned non-secret defaults (all environments)
params/<APP_ENV>/params.yml  ← versioned env overrides (dev / pre / prod)
.env                         ← secrets only, git-ignored
System environment variables ← highest priority
```

`APP_ENV` defaults to `dev`. Set it to `pre` or `prod` in your deployment environment (via `.env` or system env).

---

## Adding a new configuration variable

**For non-secret values** (feature flags, limits, URLs, etc.):
1. Add the field to `app/core/config.py` with `Field(..., description="...")`
2. Add the default value under the appropriate section of `params/base/params.yml`
3. Add env-specific overrides to `params/{dev,pre,prod}/params.yml` where the default differs
4. Add a `_flatten_yaml()` mapping in `app/core/config.py` if the YAML key differs from the field name
5. Update the variable reference table below

**For secret values** (API keys, tokens, passwords, database URLs):
1. Add the field to `app/core/config.py` with `Field(default="", description="...")`
2. Add a commented placeholder to `.env.example`
3. Update the variable reference table below

**Never add secrets to any `params/*.yml` file.**

---

## Example files (versioned)

| File | Purpose |
|------|---------|
| `params/base/params.yml` | Shared non-secret defaults (all environments) |
| `params/dev/params.yml` | Dev overrides (relaxed limits, auth disabled) |
| `params/pre/params.yml` | Pre-production overrides (semi-strict) |
| `params/prod/params.yml` | Production overrides (strict, API key required) |
| `.env.example` | Template for secrets file — never contains real values |

---

## Variables reference

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `dev` | Environment name: `dev`, `pre`, `prod` |
| `APP_DEBUG` | `True` | Enable debug mode (disable in prod) |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openrouter` | Provider name: `openrouter`, `openai`, or `deepseek` |
| `LLM_MODEL` | `meta-llama/llama-3.1-8b-instruct` | Model slug |
| `OPENROUTER_API_KEY` | — | API key (never commit) |
| `OPENAI_API_KEY` | — | API key (never commit) |
| `DEEPSEEK_API_KEY` | — | API key (never commit) |

### RAG / Embeddings

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_ENABLED` | `false` | Enable RAG knowledge layer |
| `RAG_BACKEND` | `supabase` | Backend name: `supabase` or `memory` |
| `RAG_CHUNK_SIZE_CHARS` | `1200` | Maximum text chunk size |
| `RAG_CHUNK_OVERLAP_CHARS` | `200` | Text chunk overlap |
| `EMBEDDING_PROVIDER` | `openai` | Embedding provider |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model slug |
| `EMBEDDING_DIMENSIONS` | `1536` | Embedding vector dimensions |
| `EMBEDDING_API_KEY` | — | Embedding API key fallback (never commit) |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `""` | Key required on POST /api/agents/*, /api/mcp/* |
| `API_KEY_ENABLED` | `false` | Set `true` to enforce the key |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated origin list — never use `*` |
| `TELEGRAM_ALLOWED_USER_IDS` | `""` | Comma-separated Telegram user IDs; empty = allow all |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Trusted host enforcement for Host header |

### Feature Flags (current status)

| Variable | Default | Runtime status |
|----------|---------|----------------|
| `ALLOW_AGENT_REGISTRATION` | `true` | Future scope (documented, not enforced in runtime yet) |
| `ENABLE_METRICS` | `false` | Future scope (no metrics pipeline yet) |
| `ENABLE_STRUCTURED_LOGS` | `false` | Partial (format flags available, not full structured telemetry) |

### Execution Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_MODEL_CALLS_PER_TURN` | `1` | LLM calls per agent turn |
| `MAX_TOOL_CALLS_PER_TURN` | `5` | Tool calls per agent turn |
| `MAX_AGENT_TURNS` | `10` | Turns per conversation session |
| `MAX_INPUT_CHARS` | `8000` | Max user input length |
| `MAX_OUTPUT_CHARS` | `12000` | Max agent output length |
| `AGENT_TIMEOUT_SECONDS` | `60` | Timeout for LLM call |

### Integrations

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_ENABLED` | `false` | Enable Telegram bot |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (never commit) |
| `MCP_ENABLED` | `false` | Enable MCP endpoints |
| `SUPABASE_URL` | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | — | Supabase anon key (never commit) |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase service key (never commit) |
| `SUPABASE_DB_URL` | — | Supabase/Postgres connection string (never commit) |
| `EMBEDDING_API_KEY` | — | Embedding API key fallback (never commit) |

---

## Rules

### 1. Never commit secrets

Variables ending in `_KEY`, `_TOKEN`, `_PASSWORD`, `_SECRET` must **never** be committed.  
Use `.env.local` or deployment environment variables for actual values.

### 2. Every new variable → all example files

When adding a new config variable:
1. Add a `Field(...)` definition to `app/core/config.py`
2. Add the variable with a safe default or comment to all four `.env.*.example` files
3. Add to this table in `docs/standards/configuration-standards.md`

### 3. Prod validation

Production config (`APP_ENV=prod`) raises a `ValueError` on startup if required settings are missing. Add validation to `app/core/config.py`:

```python
@model_validator(mode="after")
def _validate_prod(self) -> "Settings":
    if self.APP_ENV == "prod":
        errors = []
        if self.API_KEY_ENABLED and not self.API_KEY:
            errors.append("API_KEY must be set when API_KEY_ENABLED=true")
        # ... add more prod checks here
        if errors:
            raise ValueError("Production config errors: " + "; ".join(errors))
    return self
```

### 4. Lazy imports for settings in core modules

To avoid circular imports, import `settings` lazily inside functions (not at module top):

```python
def my_function():
    from app.core.config import settings  # lazy import
    return settings.SOME_VALUE
```

### 5. CORS never uses wildcard

`CORS_ALLOWED_ORIGINS` must always be a comma-separated list of explicit origins. The application code rejects `*` even if accidentally set.

---

## Local development quick start

```bash
cp .env.base.example .env.base
cp .env.dev.example .env.dev
# Edit .env.local with your real API keys
echo "OPENROUTER_API_KEY=sk-..." >> .env.local
```
