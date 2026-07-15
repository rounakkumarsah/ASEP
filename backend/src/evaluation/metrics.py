"""
ASEP — Evaluation Metrics Models & Collector
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.agent.events import AgentEvent, AgentEventType


# ─────────────────────────────────────────────────────────────────────────────
# Fine-grained metric models
# ─────────────────────────────────────────────────────────────────────────────

class LatencyMetrics(BaseModel):
    """Timing breakdown across session phases (all values in milliseconds)."""
    context_ms: float = 0.0
    planning_ms: float = 0.0
    execution_ms: float = 0.0
    total_ms: float = 0.0


class TaskMetrics(BaseModel):
    """Per-task execution details captured from the event stream."""
    task_id: str
    status: str = "unknown"
    duration_ms: float = 0.0
    attempts: int = 1
    tool_name: str | None = None


class MemoryMetrics(BaseModel):
    """Memory layer usage inferred from MEMORY_UPDATED events."""
    total_memory_events: int = 0
    layers_used: list[str] = Field(default_factory=list)
    episodic_writes: int = 0
    semantic_writes: int = 0
    working_updates: int = 0


class SessionMetrics(BaseModel):
    """Aggregated metrics for a complete evaluation session."""
    # Identity — all four IDs preserved per requirement
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str

    # Execution counts
    task_count: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    cancelled: int = 0
    tool_invocations: int = 0

    # Sub-metric objects
    latency: LatencyMetrics = Field(default_factory=LatencyMetrics)
    memory: MemoryMetrics = Field(default_factory=MemoryMetrics)
    per_task: list[TaskMetrics] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Collector
# ─────────────────────────────────────────────────────────────────────────────

class MetricsCollector:
    """Builds a SessionMetrics object by processing an ordered list of AgentEvents."""

    def collect(
        self,
        events: list[AgentEvent],
        session_id: str,
        run_id: str,
        thread_id: str,
        trace_id: str,
    ) -> SessionMetrics:
        metrics = SessionMetrics(
            session_id=session_id,
            run_id=run_id,
            thread_id=thread_id,
            trace_id=trace_id,
        )

        # Phase timestamps for latency computation
        _session_start: datetime | None = None
        _context_end: datetime | None = None
        _plan_end: datetime | None = None
        _session_end: datetime | None = None

        # Scratch tracking
        _task_starts: dict[str, datetime] = {}
        _task_tools: dict[str, str] = {}
        _memory_layers: set[str] = set()

        for ev in events:
            etype = ev.event_type

            if etype == AgentEventType.SESSION_STARTED:
                _session_start = ev.timestamp

            elif etype == AgentEventType.CONTEXT_BUILT:
                _context_end = ev.timestamp

            elif etype == AgentEventType.PLAN_CREATED:
                _plan_end = ev.timestamp
                metrics.task_count = ev.payload.get("task_count", 0)
                # Extract tool names from plan
                for t in ev.payload.get("tasks", []):
                    if t.get("tool_name"):
                        _task_tools[t["id"]] = t["tool_name"]

            elif etype == AgentEventType.TASK_STARTED:
                tid = ev.payload.get("task_id") or ""
                _task_starts[tid] = ev.timestamp

            elif etype in (AgentEventType.TASK_COMPLETED, AgentEventType.TASK_FAILED, AgentEventType.TASK_SKIPPED):
                tid = ev.payload.get("task_id") or ""
                status = ev.payload.get("status", "unknown")
                start = _task_starts.get(tid)
                dur = (ev.timestamp - start).total_seconds() * 1000 if start else 0.0
                metrics.per_task.append(TaskMetrics(
                    task_id=tid,
                    status=status,
                    duration_ms=dur,
                    tool_name=_task_tools.get(tid),
                ))
                if etype == AgentEventType.TASK_COMPLETED:
                    metrics.succeeded += 1
                elif etype == AgentEventType.TASK_FAILED:
                    metrics.failed += 1
                elif etype == AgentEventType.TASK_SKIPPED:
                    metrics.skipped += 1

            elif etype in (AgentEventType.TOOL_CALLED, AgentEventType.TOOL_SUCCEEDED, AgentEventType.TOOL_FAILED):
                if etype == AgentEventType.TOOL_CALLED:
                    metrics.tool_invocations += 1

            elif etype == AgentEventType.MEMORY_UPDATED:
                layer = ev.payload.get("layer", "unknown")
                _memory_layers.add(layer)
                metrics.memory.total_memory_events += 1
                if layer == "episodic":
                    metrics.memory.episodic_writes += 1
                elif layer == "semantic":
                    metrics.memory.semantic_writes += 1
                elif layer == "working":
                    metrics.memory.working_updates += 1

            elif etype in (AgentEventType.SESSION_COMPLETED, AgentEventType.SESSION_CANCELLED, AgentEventType.SESSION_FAILED):
                _session_end = ev.timestamp

        # Compute latencies
        if _session_start and _context_end:
            metrics.latency.context_ms = (_context_end - _session_start).total_seconds() * 1000
        if _context_end and _plan_end:
            metrics.latency.planning_ms = (_plan_end - _context_end).total_seconds() * 1000
        if _plan_end and _session_end:
            metrics.latency.execution_ms = (_session_end - _plan_end).total_seconds() * 1000
        if _session_start and _session_end:
            metrics.latency.total_ms = (_session_end - _session_start).total_seconds() * 1000

        metrics.memory.layers_used = sorted(_memory_layers)
        return metrics
