"""
ASEP — Model Context Protocol (MCP) Client Abstraction
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from src.tools.metadata import ToolMetadata, ToolType
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger(__name__)


class ToolClient(ABC):
    """Abstract interface representing any client connected to a tool provider (local or remote)."""

    @abstractmethod
    async def list_tools(self) -> list[ToolMetadata]:
        """Expose list of tools declared by the provider."""
        pass

    @abstractmethod
    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> ToolExecutionOutput:
        """Forward tool execution request to the provider."""
        pass


class MCPClient(ToolClient):
    """Model Context Protocol (MCP) client managing transport states.
    
    This class is configured as a virtual client for the infrastructure-only phase.
    """

    def __init__(self, server_url: str, client_id: str = "asep_mcp") -> None:
        self.server_url = server_url
        self.client_id = client_id
        self.connected = False

    async def connect(self) -> bool:
        """Simulates std_io/SSE handshake with an MCP server."""
        logger.info(f"Connecting to MCP server at {self.server_url}")
        self.connected = True
        return True

    async def list_tools(self) -> list[ToolMetadata]:
        if not self.connected:
            return []
        
        # Returns virtual remote tool metadata
        return [
            ToolMetadata(
                name="mcp_web_search",
                description="Perform google searches on remote pages.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword query"}
                    },
                    "required": ["query"]
                },
                required_permissions=["web:search"],
                tool_type=ToolType.MCP
            )
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> ToolExecutionOutput:
        if not self.connected:
            return ToolExecutionOutput(success=False, error="MCP Client is not connected.")
            
        if name != "mcp_web_search":
            return ToolExecutionOutput(success=False, error=f"Tool '{name}' not found on remote server.")

        # Simulate execution
        logger.info(f"Forwarding execution of {name} to MCP server {self.server_url}")
        query = arguments.get("query", "")
        return ToolExecutionOutput(
            success=True,
            result={"query": query, "hits": [f"Mock result for search: {query}"]}
        )

    async def disconnect(self) -> None:
        self.connected = False
        logger.info(f"Disconnected from MCP server: {self.server_url}")
