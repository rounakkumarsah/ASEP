from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    MEMORY = "memory"
    EXECUTOR = "executor"
    REFLECTOR = "reflector"
    EVALUATOR = "evaluator"
    GOVERNANCE = "governance"

class AgentState(str, Enum):
    IDLE = "Idle"
    QUEUED = "Queued"
    RUNNING = "Running"
    WAITING = "Waiting"
    RETRYING = "Retrying"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    TIMED_OUT = "TimedOut"

class AgentEventName(str, Enum):
    SUPERVISOR_STARTED = "SupervisorStarted"
    SUPERVISOR_COMPLETED = "SupervisorCompleted"
    AGENT_STARTED = "AgentStarted"
    AGENT_COMPLETED = "AgentCompleted"
    AGENT_FAILED = "AgentFailed"
    AGENT_RETRY = "AgentRetry"
    AGENT_TIMEOUT = "AgentTimeout"
    AGENT_WAITING = "AgentWaiting"
    AGENT_CANCELLED = "AgentCancelled"

class AgentManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str
    capabilities: List[str] = Field(default_factory=list)
    supported_inputs: List[str] = Field(default_factory=list)
    supported_outputs: List[str] = Field(default_factory=list)

class AgentEvent(BaseModel):
    event_id: str
    execution_id: str
    correlation_id: str
    event_name: AgentEventName
    agent_role: AgentRole
    message: str
    timestamp: float
    payload: Dict[str, Any] = Field(default_factory=dict)

class AgentRequest(BaseModel):
    execution_id: str
    correlation_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0

class AgentResponse(BaseModel):
    execution_id: str
    correlation_id: str
    status: AgentState
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    usage_metrics: Dict[str, Any] = Field(default_factory=dict)
