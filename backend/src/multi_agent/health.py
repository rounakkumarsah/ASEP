from __future__ import annotations
import logging
from src.multi_agent.contracts import AgentRole, AgentManifest
from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.registry import AgentRegistry

logger = logging.getLogger(__name__)

async def multi_agent_health_check() -> bool:
    """Verifies that the agent registry and base agents can initialize and route."""
    try:
        registry = AgentRegistry()

        class DummyAgent(BaseAgent):
            def __init__(self):
                m = AgentManifest(name="Dummy", description="Dummy healthcheck agent")
                super().__init__(role=AgentRole.PLANNER, manifest=m)
            async def _execute_internal(self, request):
                return {}

        agent = DummyAgent()
        registry.register(agent)
        
        assert registry.lookup(AgentRole.PLANNER) is not None
        assert registry.health()[AgentRole.PLANNER.value] is True
        
        logger.info("Multi-agent health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Multi-agent health check failed: {exc}")
        return False
