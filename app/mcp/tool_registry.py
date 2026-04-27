"""MCP tool registry."""

from app.mcp import MCPServer

# Global MCP server instance
_mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Get the global MCP server."""
    return _mcp_server
