"""
ASEP — Unified Tool Discovery
"""

import logging

from src.tools.mcp_client import ToolClient
from src.tools.metadata import ToolMetadata
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolDiscovery:
    """Consolidates local registry tools and active remote client tools into a single directory."""

    def __init__(self, registry: ToolRegistry, mcp_clients: list[ToolClient] | None = None) -> None:
        self.registry = registry
        self.mcp_clients = mcp_clients or []

    async def list_available_tools(self) -> list[ToolMetadata]:
        """Aggregate metadata of all local and remote tools."""
        available_tools: list[ToolMetadata] = []
        
        # 1. Local tools
        for tool in self.registry.get_all().values():
            available_tools.append(tool.get_metadata())
            
        # 2. Remote MCP tools
        for client in self.mcp_clients:
            try:
                remote_tools = await client.list_tools()
                available_tools.extend(remote_tools)
            except Exception as e:
                logger.error(f"Failed to fetch tools from remote client: {e}")
                
        return available_tools
