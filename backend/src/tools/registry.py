"""
ASEP — Tool Registry
"""

import logging
from typing import Dict, List, Optional
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Manages system-wide registration, discovery, enabling/disabling of tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._enabled_states: Dict[str, bool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting registered tool: '{tool.name}'")
        self._tools[tool.name] = tool
        self._enabled_states[tool.name] = True
        logger.debug(f"ToolRegistry: registered tool '{tool.name}'")

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            if name in self._enabled_states:
                del self._enabled_states[name]
            logger.debug(f"ToolRegistry: unregistered tool '{name}'")

    def lookup(self, name: str) -> Optional[BaseTool]:
        """Lookup a registered tool instance by name."""
        return self._tools.get(name)

    def discover(self, capability: Optional[str] = None) -> List[BaseTool]:
        """Discover tools matching a specific capability or category."""
        results = []
        for tool in self._tools.values():
            if not self._enabled_states.get(tool.name, False):
                continue
            if capability:
                caps = tool.capabilities()
                if (
                    caps.get(capability) is True or 
                    capability in tool.metadata().required_permissions or 
                    tool.category.lower() == capability.lower()
                ):
                    results.append(tool)
            else:
                results.append(tool)
        return results

    def enable(self, name: str) -> None:
        """Enable a tool by name."""
        if name in self._tools:
            self._enabled_states[name] = True
            logger.info(f"ToolRegistry: enabled tool '{name}'")

    def disable(self, name: str) -> None:
        """Disable a tool by name."""
        if name in self._tools:
            self._enabled_states[name] = False
            logger.info(f"ToolRegistry: disabled tool '{name}'")

    def is_enabled(self, name: str) -> bool:
        """Check if a tool is enabled."""
        return self._enabled_states.get(name, False)

    def get_all(self) -> Dict[str, BaseTool]:
        """Get all registered tool instances."""
        return self._tools

    def health(self) -> Dict[str, dict]:
        """Get diagnostic health of all active tools."""
        statuses = {}
        for name, tool in self._tools.items():
            if self._enabled_states.get(name, False):
                try:
                    statuses[name] = tool.health()
                except Exception as e:
                    statuses[name] = {"status": "unhealthy", "available": False, "error": str(e)}
        return statuses

    def version(self, name: str) -> Optional[str]:
        """Get version of a registered tool."""
        tool = self._tools.get(name)
        return tool.version if tool else None
