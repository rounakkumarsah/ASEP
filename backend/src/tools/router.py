"""
ASEP — Tool Routing and Permission Enforcement
"""

import logging
from typing import Any

from src.tools.mcp_client import ToolClient
from src.tools.permissions import verify_tool_permissions
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger(__name__)


class ToolRouter:
    """Dispatches execution requests to local or remote tools after checking permissions."""

    def __init__(self, registry: ToolRegistry, mcp_clients: list[ToolClient] | None = None) -> None:
        self.registry = registry
        self.mcp_clients = mcp_clients or []

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        granted_permissions: list[str]
    ) -> ToolExecutionOutput:
        """Route tool execution requests and enforce safety controls."""
        logger.info(f"Routing request for tool: '{tool_name}'")
        
        # 1. Resolve Local Tool
        local_tool = self.registry.get_tool(tool_name)
        if local_tool:
            # Enforce Permission Guard
            authorized, reason = verify_tool_permissions(local_tool.required_permissions, granted_permissions)
            if not authorized:
                logger.warning(f"Permission denied for '{tool_name}': {reason}")
                return ToolExecutionOutput(success=False, error=reason)
                
            return await local_tool.run(arguments)

        # 2. Resolve Remote MCP Tool
        for client in self.mcp_clients:
            try:
                tools = await client.list_tools()
                for tool in tools:
                    if tool.name == tool_name:
                        # Enforce Permission Guard
                        authorized, reason = verify_tool_permissions(tool.required_permissions, granted_permissions)
                        if not authorized:
                            logger.warning(f"Permission denied for remote '{tool_name}': {reason}")
                            return ToolExecutionOutput(success=False, error=reason)
                            
                        return await client.execute_tool(tool_name, arguments)
            except Exception as e:
                logger.error(f"Error checking tools on MCP client: {e}")

        # 3. Fallback: Not Found
        logger.error(f"Tool '{tool_name}' could not be resolved.")
        return ToolExecutionOutput(success=False, error=f"Tool '{tool_name}' not found.")
