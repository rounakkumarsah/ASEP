"""
ASEP — Control Plane Agents
"""

from src.multi_agent.registry import AgentRegistry
from src.multi_agent.contracts import AgentRole


class AgentManager:
    """Read-only view over registered specialized agents."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def list_agents(self) -> list[dict]:
        """Returns metadata about initialized agents in the registry."""
        agents_info = []
        for role in self._registry.registered_roles():
            agent_instance = self._registry.get(role)
            agents_info.append({
                "role": role.value,
                "status": "online" if agent_instance else "offline",
                "class": agent_instance.__class__.__name__ if agent_instance else None
            })
        return agents_info
