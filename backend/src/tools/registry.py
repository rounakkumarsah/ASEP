"""
ASEP — Tool Registry
"""

import logging

from src.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Manages system-wide registration and retrieval of local tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a local tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting registered tool: '{tool.name}'")
        self._tools[tool.name] = tool
        logger.debug(f"ToolRegistry: registered local tool '{tool.name}'")

    def get_tool(self, name: str) -> BaseTool | None:
        """Retrieve a registered local tool instance by name."""
        return self._tools.get(name)

    def get_all(self) -> dict[str, BaseTool]:
        """Get all registered local tool instances."""
        return self._tools
