"""
ASEP — Trajectory Analysis

Converts a raw AgentEvent stream into a structured step-by-step trajectory and
computes derived path metrics. Valid alternative execution paths are not penalized —
the scorer rewards final success regardless of which route was taken.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from src.agent.events import AgentEvent, AgentEventType


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

class TrajectoryStep(BaseModel):
    """One observable step in the agent's execution path."""
    step_index: int
    event_type: str
    task_id: str | None = None
    tool_name: str | None = None
    status: str | None = None
    timestamp: datetime
    payload_summary: dict[str, Any] = Field(default_factory=dict)


class Trajectory(BaseModel):
    """Complete, ordered execution path for a single evaluation run.

    All four run identifiers are preserved for cross-referencing.
    """
    session_id: str
    thread_id: str
    run_id: str
    trace_id: str
    steps: list[TrajectoryStep] = Field(default_factory=list)
    plan_task_count: int = 0

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def task_steps(self) -> list[TrajectoryStep]:
        return [
            s for s in self.steps
            if s.event_type in (
                AgentEventType.TASK_STARTED.value,
                AgentEventType.TASK_COMPLETED.value,
                AgentEventType.TASK_FAILED.value,
                AgentEventType.TASK_SKIPPED.value,
            )
        ]


class TrajectoryAnalysis(BaseModel):
    """Derived metrics computed from a Trajectory."""
    total_steps: int = 0
    planning_steps: int = 0
    execution_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    tool_steps: int = 0
    memory_steps: int = 0
    succeeded_tasks: int = 0

    # Path quality
    path_efficiency_ratio: float = 0.0
    """succeeded_tasks / plan_task_count — 1.0 = all planned tasks succeeded."""
    steps_per_task: float = 0.0
    """execution_steps / plan_task_count — lower means less overhead per task."""
    had_cancellation: bool = False

    # Alternative path tolerance
    valid_alternative_path: bool = False
    """True if the session completed successfully despite a different step count
    than the plan_task_count. Ensures regression tests pass on equivalent alternatives."""


# ─────────────────────────────────────────────────────────────────────────────
# Analyser
# ─────────────────────────────────────────────────────────────────────────────

# Events that count as "planning" steps
_PLANNING_EVENT_TYPES = {
    AgentEventType.SESSION_STARTED.value,
    AgentEventType.CONTEXT_BUILT.value,
    AgentEventType.PLAN_CREATED.value,
}

# Events that count as "execution" steps
_EXECUTION_EVENT_TYPES = {
    AgentEventType.TASK_STARTED.value,
    AgentEventType.TASK_COMPLETED.value,
    AgentEventType.TASK_FAILED.value,
    AgentEventType.TASK_SKIPPED.value,
}

_TOOL_EVENT_TYPES = {
    AgentEventType.TOOL_CALLED.value,
    AgentEventType.TOOL_SUCCEEDED.value,
    AgentEventType.TOOL_FAILED.value,
}

_MEMORY_EVENT_TYPES = {AgentEventType.MEMORY_UPDATED.value}

_TERMINAL_EVENT_TYPES = {
    AgentEventType.SESSION_COMPLETED.value,
    AgentEventType.SESSION_FAILED.value,
    AgentEventType.SESSION_CANCELLED.value,
}


class TrajectoryAnalyzer:
    """Builds a Trajectory from an AgentEvent list and derives path analysis."""

    def build_from_events(
        self,
        events: list[AgentEvent],
        session_id: str,
        thread_id: str,
        run_id: str,
        trace_id: str,
    ) -> Trajectory:
        """Convert a raw AgentEvent stream into an indexed Trajectory."""
        trajectory = Trajectory(
            session_id=session_id,
            thread_id=thread_id,
            run_id=run_id,
            trace_id=trace_id,
        )

        for idx, ev in enumerate(events):
            # Slim payload summary — avoid carrying full nested dicts
            summary: dict[str, Any] = {}
            for key in ("task_id", "status", "tool_name", "detail", "error", "task_count", "layer"):
                if key in ev.payload:
                    summary[key] = ev.payload[key]

            step = TrajectoryStep(
                step_index=idx,
                event_type=ev.event_type.value,
                task_id=ev.payload.get("task_id"),
                tool_name=ev.payload.get("tool_name"),
                status=ev.payload.get("status"),
                timestamp=ev.timestamp,
                payload_summary=summary,
            )
            trajectory.steps.append(step)

            # Extract plan_task_count from PLAN_CREATED event
            if ev.event_type == AgentEventType.PLAN_CREATED:
                trajectory.plan_task_count = ev.payload.get("task_count", 0)

        return trajectory

    def analyze(self, trajectory: Trajectory) -> TrajectoryAnalysis:
        """Compute derived metrics from a built trajectory."""
        analysis = TrajectoryAnalysis(total_steps=trajectory.total_steps)

        session_completed = False
        session_cancelled = False

        for step in trajectory.steps:
            et = step.event_type

            if et in _PLANNING_EVENT_TYPES:
                analysis.planning_steps += 1

            elif et in _EXECUTION_EVENT_TYPES:
                analysis.execution_steps += 1
                if et == AgentEventType.TASK_COMPLETED.value:
                    analysis.succeeded_tasks += 1
                elif et == AgentEventType.TASK_FAILED.value:
                    analysis.failed_steps += 1
                elif et == AgentEventType.TASK_SKIPPED.value:
                    analysis.skipped_steps += 1

            elif et in _TOOL_EVENT_TYPES:
                analysis.tool_steps += 1

            elif et in _MEMORY_EVENT_TYPES:
                analysis.memory_steps += 1

            elif et == AgentEventType.SESSION_COMPLETED.value:
                session_completed = True
            elif et == AgentEventType.SESSION_CANCELLED.value:
                session_cancelled = True

        analysis.had_cancellation = session_cancelled

        plan_count = trajectory.plan_task_count or 1  # avoid division by zero

        # Path efficiency: what fraction of planned tasks succeeded
        analysis.path_efficiency_ratio = round(
            analysis.succeeded_tasks / plan_count, 4
        )

        # Steps per task: execution overhead per planned task
        analysis.steps_per_task = round(
            analysis.execution_steps / plan_count, 4
        )

        # Valid alternative path: session completed AND all tasks that ran succeeded
        # (even if step count differs from plan_task_count)
        analysis.valid_alternative_path = (
            session_completed
            and analysis.succeeded_tasks > 0
            and analysis.failed_steps == 0
        )

        return analysis
