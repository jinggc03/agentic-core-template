"""MCP endpoint."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from app.mcp.tool_registry import get_mcp_server
from app.api.deps import require_api_key

router = APIRouter()


class MCPToolDefinition(BaseModel):
    """MCP tool definition."""

    id: str
    description: str
    inputSchema: Dict[str, Any]


class MCPToolCallRequest(BaseModel):
    """MCP tool call request."""

    tool_id: str
    arguments: Dict[str, Any]


@router.get("/info", tags=["mcp"])
async def mcp_info():
    """Get MCP server info.
    
    Returns:
        Server information
    """
    server = get_mcp_server()
    return server.get_server_info()


@router.get("/tools", tags=["mcp"])
async def list_mcp_tools():
    """List available MCP tools.
    
    Returns:
        List of tool definitions
    """
    server = get_mcp_server()
    tools = server.list_tools()
    return {"tools": tools, "count": len(tools)}


@router.get("/resources", tags=["mcp"])
async def list_mcp_resources():
    """List available MCP resources.
    
    Returns:
        List of resource IDs
    """
    server = get_mcp_server()
    resources = server.list_resources()
    return {"resources": resources, "count": len(resources)}


@router.post("/tools/call", tags=["mcp"])
async def call_mcp_tool(request: MCPToolCallRequest, _: str = Depends(require_api_key)):
    """Call an MCP tool.
    
    Args:
        request: Tool call request
        
    Returns:
        Tool result
    """
    try:
        server = get_mcp_server()
        result = await server.handle_tool_call(request.tool_id, request.arguments)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
