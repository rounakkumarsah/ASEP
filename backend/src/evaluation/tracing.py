"""
ASEP — Internal Span-Based Tracing

Pure in-memory tracing. No OpenTelemetry dependency in this phase.
DB/OTEL export hooks are reserved for a future phase.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator

from pydantic import BaseModel, Field


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"
    RUNNING = "running"


class TraceSpan(BaseModel):
    """An individual unit of traced work within a session."""
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: str | None = None
    name: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    end_time: datetime | None = None
    status: SpanStatus = SpanStatus.RUNNING
    attributes: dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


class Trace(BaseModel):
    """Complete trace of a single evaluation session."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    thread_id: str
    run_id: str
    spans: list[TraceSpan] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def add_span(self, span: TraceSpan) -> None:
        self.spans.append(span)

    @property
    def root_spans(self) -> list[TraceSpan]:
        return [s for s in self.spans if s.parent_span_id is None]

    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms or 0.0 for s in self.spans if s.parent_span_id is None)


class _SpanContext:
    """Async context manager returned by Tracer.span()."""

    def __init__(
        self,
        trace: Trace,
        name: str,
        parent_span_id: str | None = None,
        **attributes: Any,
    ) -> None:
        self._trace = trace
        self._span = TraceSpan(
            name=name,
            parent_span_id=parent_span_id,
            attributes=attributes,
        )

    async def __aenter__(self) -> TraceSpan:
        return self._span

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._span.end_time = datetime.now(tz=timezone.utc)
        if exc_type is not None:
            self._span.status = SpanStatus.ERROR
            self._span.attributes["error"] = str(exc_val)
        else:
            self._span.status = SpanStatus.OK
        self._trace.add_span(self._span)


class Tracer:
    """Creates and records spans into an associated Trace."""

    def __init__(self, trace: Trace) -> None:
        self._trace = trace

    def span(
        self,
        name: str,
        parent_span_id: str | None = None,
        **attributes: Any,
    ) -> _SpanContext:
        """Return an async context manager that times and records a span."""
        return _SpanContext(self._trace, name, parent_span_id, **attributes)

    @property
    def trace(self) -> Trace:
        return self._trace


class TraceStore:
    """In-memory trace storage with a persistence hook for future DB/OTEL integration."""

    def __init__(self) -> None:
        self._traces: dict[str, Trace] = {}

    def add(self, trace: Trace) -> None:
        self._traces[trace.trace_id] = trace

    def get(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    def list_all(self) -> list[Trace]:
        return list(self._traces.values())

    def clear(self) -> None:
        self._traces.clear()

    def __len__(self) -> int:
        return len(self._traces)
