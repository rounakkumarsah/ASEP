"""
ASEP — Tooling Infrastructure Health Check
"""

import logging

from src.tools.impl import ConfigurationTool
from src.tools.mcp_client import MCPClient
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def tool_infrastructure_health_check() -> bool:
    """Validates that local registry and MCP client transport layers are functional.
    
    Returns:
        True if tooling configurations resolve and mock handshakes succeed, False otherwise.
    """
    try:
        # 1. Local Registration Verification
        registry = ToolRegistry()
        registry.register(ConfigurationTool())
        if not registry.lookup("configuration"):
            return False
            
        # 2. Remote Client Lifecycle Validation
        client = MCPClient(server_url="http://mock-mcp-server:8000")
        connected = await client.connect()
        if not connected:
            return False
            
        await client.disconnect()
        logger.info("Tool infrastructure health check passed.")
        return True
    except Exception as e:
        logger.warning(f"Tool infrastructure health check failed: {e}")
        return False
