"""
ASEP — Multi-Agent Health Check
"""

import asyncio
import logging

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext
from src.multi_agent.messaging import MessageBus
from src.multi_agent.registry import AgentRegistry

logger = logging.getLogger(__name__)


async def multi_agent_health_check() -> bool:
    """Verifies that the message bus and registry can initialize and route messages."""
    try:
        bus = MessageBus()
        registry = AgentRegistry()

        # Dummy Agent
        class DummyAgent:
            def __init__(self):
                self.role = AgentRole.PLANNER
        
        registry.register(AgentRole.PLANNER, DummyAgent())
        assert registry.get(AgentRole.PLANNER) is not None

        # Test message passing
        msg = Message(
            session_id="hc",
            run_id="hc",
            thread_id="hc",
            trace_id="hc",
            sender_role=AgentRole.SUPERVISOR,
            receiver_role=AgentRole.PLANNER,
            message_type=MessageType.REQUEST,
            payload={"test": "data"}
        )

        await bus.publish(msg)
        
        # Subscribe and get message
        async for received in bus.subscribe(AgentRole.PLANNER):
            assert received.message_id == msg.message_id
            break

        logger.info("Multi-agent health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Multi-agent health check failed: {exc}")
        return False
