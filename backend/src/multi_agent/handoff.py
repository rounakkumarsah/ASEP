"""
ASEP — Handoff Protocol
"""

from typing import Any

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext


class HandoffManager:
    """Standardizes handoff messages between agents."""

    @staticmethod
    def create_handoff(
        context: CoordinationContext,
        from_role: AgentRole,
        to_role: AgentRole,
        payload: dict[str, Any]
    ) -> Message:
        """Create a HANDOFF message indicating transition of control."""
        return Message(
            session_id=context.session_id,
            run_id=context.run_id,
            thread_id=context.thread_id,
            trace_id=context.trace_id,
            sender_role=from_role,
            receiver_role=to_role,
            message_type=MessageType.HANDOFF,
            payload=payload,
        )
