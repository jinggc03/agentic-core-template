#!/bin/bash
# Run MCP server

cd "$(dirname "$0")/.."
python -m app.mcp.server
