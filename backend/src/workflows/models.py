"""
ASEP — Workflows Models & Structures
"""

import time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_HITL = "WAITING_HITL"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowEvent(StrEnum):
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
    retry_conditions: list[str] = Field(default_factory=list)  # error substring conditions


class CheckpointPolicy(BaseModel):
    on_step_complete: bool = True
    on_failure: bool = True


class WorkflowStep(BaseModel):
    node_id: str
    description: str = ""
    target_agent: str = "default_agent"
    target_tool: str | None = None
    next_node: str | None = None  # None indicates execution graph ending
    conditional_routes: dict[str, str] | None = None  # outcome -> node_id mapping
    parallel_nodes: list[str] | None = None  # fan-out node ids
    join_node: str | None = None  # fan-in node id



class WorkflowDefinition(BaseModel):
    workflow_id: str
    version: str = "1.0.0"
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)

    output_schema: dict[str, Any] = Field(default_factory=dict)
    required_agents: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    timeout: float = 3600.0  # Default 1 hour
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    checkpoint_policy: CheckpointPolicy = Field(default_factory=CheckpointPolicy)
    steps: list[WorkflowStep] = Field(default_factory=list)
    is_enabled: bool = True


class WorkflowContext(BaseModel):
    workflow_id: str
    execution_id: str
    correlation_id: str = "default_corr"
    session_id: str = "default_session"
    project_id: str = "default_project"

    memory_ids: list[str] = Field(default_factory=list)
    retrieved_documents: list[str] = Field(default_factory=list)


class Checkpoint(BaseModel):
    execution_id: str
    workflow_state: ExecutionState
    current_node: str | None = None
    completed_nodes: list[str] = Field(default_factory=list)
    pending_nodes: list[str] = Field(default_factory=list)
    agent_outputs: dict[str, Any] = Field(default_factory=dict)
    tool_outputs: dict[str, Any] = Field(default_factory=dict)
    memory_references: list[str] = Field(default_factory=list)
    approval_state: str | None = None
    timestamp: float = Field(default_factory=time.time)


class WorkflowHistory(BaseModel):
    execution_id: str
    workflow_id: str
    state_transitions: list[dict[str, Any]] = Field(default_factory=list)
    retries: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    execution_duration: float = 0.0
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
