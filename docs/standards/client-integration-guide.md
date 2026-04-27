# Client Integration Guide

This guide explains how external systems interact with the agentic-core API — including REST, Telegram, and future surfaces.

---

## REST API

### Authentication

All `POST` endpoints under `/api/agents/*` and `/api/mcp/*` require:

```
X-API-Key: <your-api-key>
```

Set `API_KEY_ENABLED=true` and `API_KEY=<value>` in your environment. See [configuration-standards.md](configuration-standards.md).

GET endpoints are public — no auth required.

### Base URL

```
http://localhost:8000/api
```

In production, replace with your deployment domain.

---

### Run an agent turn

```http
POST /api/agents/run
X-API-Key: your-api-key
Content-Type: application/json

{
  "agent_id": "invoice-agent",
  "input": "Create an invoice for Acme Corp, $500 for consulting",
  "conversation_id": "conv-abc123"  // optional — for session continuity
}
```

Alternative route when the agent ID is in the URL:

```http
POST /api/agents/{agent_id}/run
X-API-Key: your-api-key
Content-Type: application/json

{
  "input": "Create an invoice for Acme Corp, $500 for consulting",
  "conversation_id": "conv-abc123"
}
```

Response:

```json
{
  "agent_id": "invoice-agent",
  "output": "Invoice created: INV-001...",
  "status": "success",
  "execution_time_ms": 123.4,
  "model_calls": 1,
  "tool_calls": 0,
  "error": null
}
```

Error response (e.g., loop detected, timeout):

```json
{
  "agent_id": "invoice-agent",
  "output": "",
  "status": "failed",
  "execution_time_ms": 60001.0,
  "model_calls": 0,
  "tool_calls": 0,
  "error": "Execution timed out after 60s",
}
```

---

### List agents

```http
GET /api/agents
```

Response:

```json
{
  "agents": ["invoice-agent"],
  "count": 1
}
```

---

### Get agent context/state

```http
GET /api/agents/{agent_id}/context
```

Returns the current state of the agent session.

---

### Reset agent session

```http
POST /api/agents/{agent_id}/reset
X-API-Key: your-api-key
```

Clears conversation history and loop guard state.

---

### MCP tools

```http
GET /api/mcp/tools           # List available tools (public)
GET /api/mcp/info            # Server metadata (public)
GET /api/mcp/resources       # List resources (public)

POST /api/mcp/tools/call     # Call a tool (requires X-API-Key)
Content-Type: application/json

{
  "tool_name": "web_search",
  "arguments": {
    "query": "latest AI news",
    "max_results": 5
  }
}
```

---

## Telegram Bot

### Setup

1. Create a bot via @BotFather and obtain the token
2. Set `TELEGRAM_ENABLED=true` and `TELEGRAM_BOT_TOKEN=<token>` in your env
3. Register the webhook: `POST https://api.telegram.org/bot<token>/setWebhook?url=https://your-domain.com/api/telegram/webhook`

### Allowlist

To restrict bot access to specific users, set:

```
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
```

Leave empty to allow all users (only do this in development).

### Interaction

Users interact with the bot via regular chat messages. Commands:

| Command | Description |
|---------|-------------|
| `/start` | Greet the user and show help |
| `/reset` | Clear conversation history |
| `/status` | Show bot status |

Non-command messages are forwarded to the default agent.

---

## Limits clients must respect

| Limit | Value | Behaviour if exceeded |
|-------|-------|----------------------|
| Max input length | 8000 chars | Returns `success: false, error: "Input too long"` |
| Max output length | 12000 chars | Output is truncated |
| Max agent turns | 10 | Returns error after limit reached |
| Request timeout | 60s | Returns `success: false, error: "Execution timed out"` |

---

## Health check

```http
GET /api/health/health
```

No authentication required. Used by load balancers and monitoring systems.

Response:

```json
{"status": "healthy"}
```

---

## Future surfaces

Additional client surfaces planned:

- **Web frontend** — React-based chat UI consuming the REST API
- **CLI** — `agentctl run --agent invoice "Create invoice for..."` 
- **Slack** — Slack app integration (same REST API backend)
- **Discord** — Discord bot integration

All surfaces use the same REST API. Authentication is always via `X-API-Key`.
