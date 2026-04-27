# MCP Integration Guide

MCP (Model Context Protocol) is the **external exposure layer** for agent skills. It lets external clients discover and invoke agent capabilities without knowing the internal agent architecture.

**Key rule:** MCP routes call skills. Skills do not call MCP.

---

## Architecture

```
External client
    │
    ▼
POST /api/mcp/tools/call   ← protected by X-API-Key
    │
    ▼
MCPToolCallRequest
    │
    ▼
Skill (app/skills/...)
    │
    ▼
Result dict
```

The MCP endpoints in `app/api/routes/mcp.py` are the only entry point. All POST routes require the `X-API-Key` header. GET routes (info, list tools, list resources) are public.

---

## Registering a tool

### 1. Implement the skill

See [skill-development-guide.md](skill-development-guide.md).

### 2. Add a tool entry to the tool registry

```python
# app/mcp/tools.py  (create if not present)
from app.skills.web_search.skill import WebSearchSkill

TOOL_REGISTRY = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        "skill": WebSearchSkill,
    }
}
```

### 3. Wire the call handler

In `app/api/routes/mcp.py`, the `call_mcp_tool` handler dispatches to the registry:

```python
@router.post("/tools/call", tags=["mcp"])
async def call_mcp_tool(
    request: MCPToolCallRequest,
    _: str = Depends(require_api_key),
):
    tool = TOOL_REGISTRY.get(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    skill = tool["skill"]()
    result = await skill.run(**request.arguments)
    return {"result": result}
```

---

## Input validation

Always validate input at the MCP handler boundary using the tool's `input_schema`. Do not trust raw arguments passed by the caller.

```python
from pydantic import BaseModel, Field, ValidationError

class WebSearchArguments(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)

# In the handler:
try:
    args = WebSearchArguments(**request.arguments)
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))

result = await skill.run(query=args.query, max_results=args.max_results)
```

---

## Protecting endpoints

All POST MCP routes **must** include the API key dependency:

```python
from app.api.deps import require_api_key
from fastapi import Depends

@router.post("/tools/call")
async def call_mcp_tool(request: ..., _: str = Depends(require_api_key)):
    ...
```

GET routes (discovery) may remain public:

```python
@router.get("/tools")
async def list_tools():  # No auth required — tool list is not sensitive
    ...
```

---

## Exposing resources

Resources (read-only data sources) follow the same pattern but use GET endpoints and do not require authentication:

```python
@router.get("/resources/{resource_name}")
async def get_resource(resource_name: str):
    ...
```

---

## MCP Info endpoint

`GET /api/mcp/info` returns server metadata:

```json
{
  "name": "agentic-core",
  "version": "1.0.0",
  "protocol": "mcp-1.0",
  "capabilities": ["tools", "resources"]
}
```

---

## Testing MCP endpoints

```python
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_list_tools_public():
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200

def test_call_tool_requires_api_key():
    response = client.post("/api/mcp/tools/call", json={...})
    assert response.status_code == 403  # No key provided

def test_call_tool_with_key():
    response = client.post(
        "/api/mcp/tools/call",
        headers={"X-API-Key": "test-key"},
        json={"tool_name": "web_search", "arguments": {"query": "hello"}},
    )
    assert response.status_code == 200
```
