"""
ASEP — Governance Intent
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field

class ActionIntent(BaseModel):
    """Explicit declaration of an intended action before execution."""
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str
    
    # RBAC and Context
    actor_role: str
    action_type: str  # e.g., "tool_execution", "memory_write"
    target: str       # e.g., "database_drop", "system_prompt"
    
    # Payload details
    payload: dict[str, Any] = Field(default_factory=dict)
    justification: str = Field(default="")
