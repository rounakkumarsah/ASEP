"""
ASEP — Multi-Agent Contracts
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    EXECUTOR = "executor"
    MEMORY = "memory"
    EVALUATOR = "evaluator"
    REFLECTOR = "reflector"


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HANDOFF = "handoff"


class Message(BaseModel):
    """Strongly typed base message payload for inter-agent communication."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str
    sender_role: AgentRole
    receiver_role: AgentRole
    message_type: MessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
