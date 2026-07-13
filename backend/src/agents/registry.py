"""
ASEP — Agent Registry (Placeholder)
======================================
Central registry that maps agent names to their factory functions.

Design goals:
  - Every agent is self-describing (name, description, capabilities)
  - Agents are discoverable at runtime
  - Registry supports hot-reload in development

TODO (Phase 0.2):
    - Implement agent registration decorator
    - Add capability-based agent selection
    - Add agent lifecycle management (start / stop / restart)
    - Integrate with governance module for access control
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Type alias for an agent factory callable
AgentFactory = Callable[..., Any]

# Global registry — populated via @register_agent decorator
_REGISTRY: dict[str, AgentFactory] = {}


def register_agent(name: str) -> Callable[[AgentFactory], AgentFactory]:
    """
    Decorator to register an agent factory in the global registry.

    Usage:
        @register_agent("code_writer")
        def create_code_writer_agent() -> CodeWriterAgent:
            return CodeWriterAgent(...)

    TODO (Phase 0.2): Validate agent interface compliance on registration.
    """
    def decorator(fn: AgentFactory) -> AgentFactory:
        if name in _REGISTRY:
            logger.warning("Agent already registered, overwriting", extra={"name": name})
        _REGISTRY[name] = fn
        logger.info("Agent registered", extra={"name": name})
        return fn
    return decorator


def get_agent(name: str) -> AgentFactory:
    """
    Retrieve a registered agent factory by name.

    Args:
        name: The agent name as provided to @register_agent.

    Returns:
        The agent factory callable.

    Raises:
        KeyError: If no agent with the given name is registered.
    """
    if name not in _REGISTRY:
        raise KeyError(f"No agent registered with name '{name}'. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]


def list_agents() -> list[str]:
    """Return all registered agent names."""
    return list(_REGISTRY.keys())
