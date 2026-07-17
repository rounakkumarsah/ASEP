"""
ASEP — Workflows Models & Structures
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_HITL = "WAITING_HITL"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowEvent(str, Enum):
    STARTED = "WorkflowStarted"
    PAUSED = "WorkflowPaused"
    RESUMED = "WorkflowResumed"
    COMPLETED = "WorkflowCompleted"
    FAILED = "WorkflowFailed"
    RETRY = "WorkflowRetry"
    CANCELLED = "WorkflowCancelled"
    CHECKPOINT_CREATED = "CheckpointCreated"
    CHECKPOINT_RESTORED = "CheckpointRestored"


class RetryPolicy(BaseModel):
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    retry_conditions: List[str] = Field(default_factory=list)  # error substring conditions


class CheckpointPolicy(BaseModel):
    on_step_complete: bool = True
    on_failure: bool = True


class WorkflowStep(BaseModel):
    node_id: str
    description: str
    target_agent: str
    target_tool: Optional[str] = None
    next_node: Optional[str] = None  # None indicates execution graph ending
    conditional_routes: Optional[Dict[str, str]] = None  # outcome -> node_id mapping
    parallel_nodes: Optional[List[str]] = None  # fan-out node ids
    join_node: Optional[str] = None  # fan-in node id


class WorkflowDefinition(BaseModel):
    workflow_id: str
    version: str = "1.0.0"
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_agents: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    timeout: float = 3600.0  # Default 1 hour
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    checkpoint_policy: CheckpointPolicy = Field(default_factory=CheckpointPolicy)
    steps: List[WorkflowStep] = Field(default_factory=list)
    is_enabled: bool = True


class WorkflowContext(BaseModel):
    workflow_id: str
    execution_id: str
    correlation_id: str
    session_id: str
    project_id: str = "default_project"
    memory_ids: List[str] = Field(default_factory=list)
    retrieved_documents: List[str] = Field(default_factory=list)


class Checkpoint(BaseModel):
    execution_id: str
    workflow_state: ExecutionState
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    pending_nodes: List[str] = Field(default_factory=list)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    tool_outputs: Dict[str, Any] = Field(default_factory=dict)
    memory_references: List[str] = Field(default_factory=list)
    approval_state: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class WorkflowHistory(BaseModel):
    execution_id: str
    workflow_id: str
    state_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    retries: List[Dict[str, Any]] = Field(default_factory=list)
    approvals: List[Dict[str, Any]] = Field(default_factory=list)
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    execution_duration: float = 0.0
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
