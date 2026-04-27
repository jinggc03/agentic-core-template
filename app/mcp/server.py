"""MCP (Model Context Protocol) server implementation."""

from typing import Dict, List, Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServer:
	"""Model Context Protocol server.

	Exposes runtime capabilities as MCP tools/resources.
	"""

	def __init__(self, name: str = "personal-agent-runtime"):
		"""Initialize MCP server.

		Args:
			name: Server name
		"""
		self.name = name
		self.tools: Dict[str, Dict[str, Any]] = {}
		self.resources: Dict[str, str] = {}

	def register_tool(
		self,
		tool_id: str,
		description: str,
		input_schema: Dict[str, Any],
		handler: Optional[callable] = None,
	) -> None:
		"""Register a tool in MCP."""
		self.tools[tool_id] = {
			"id": tool_id,
			"description": description,
			"inputSchema": input_schema,
			"handler": handler,
		}
		logger.info(f"Registered MCP tool: {tool_id}")

	def register_resource(self, resource_id: str, content: str) -> None:
		"""Register a resource in MCP."""
		self.resources[resource_id] = content
		logger.info(f"Registered MCP resource: {resource_id}")

	def list_tools(self) -> List[Dict[str, Any]]:
		"""List all available tools."""
		return [
			{k: v for k, v in tool.items() if k != "handler"}
			for tool in self.tools.values()
		]

	def list_resources(self) -> List[str]:
		"""List all available resources."""
		return list(self.resources.keys())

	async def handle_tool_call(self, tool_id: str, arguments: Dict[str, Any]) -> Any:
		"""Handle a tool call."""
		if tool_id not in self.tools:
			raise ValueError(f"Tool not found: {tool_id}")

		tool = self.tools[tool_id]
		handler = tool.get("handler")

		if handler is None:
			return {"error": f"No handler for tool: {tool_id}"}

		try:
			result = handler(**arguments)
			if hasattr(result, "__await__"):
				result = await result
			return {"result": result}
		except Exception as e:
			logger.error(f"Tool error {tool_id}: {e}")
			return {"error": str(e)}

	def get_server_info(self) -> Dict[str, Any]:
		"""Get server information."""
		return {
			"name": self.name,
			"version": "0.1.0",
			"tools_count": len(self.tools),
			"resources_count": len(self.resources),
		}
