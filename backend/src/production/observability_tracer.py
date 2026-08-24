"""
ASEP — Agent Observability Tracer
===================================
Captures execution, planner, workflow, tool, memory, and GraphRAG traces,
token consumption, latency metrics, and USD cost tracking.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ObservabilitySpan:
    span_id: str
    trace_id: str
    component: str  # planner, workflow, tool, memory, graphrag, agent
    name: str
    start_time: float
    end_time: float | None = None
    status: str = "ok"
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


class AgentObservabilityTracer:
    """Central tracer for agent operations, metrics, and cost aggregation."""

    def __init__(self) -> None:
        self._spans: list[ObservabilitySpan] = []

    def start_span(
        self,
        span_id: str,
        trace_id: str,
        component: str,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> ObservabilitySpan:
        span = ObservabilitySpan(
            span_id=span_id,
            trace_id=trace_id,
            component=component,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        self._spans.append(span)
        logger.info("Trace [%s] started span '%s' (%s)", trace_id, name, component)
        return span

    def end_span(
        self,
        span_id: str,
        status: str = "ok",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        for span in self._spans:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.status = status
                span.tokens_used = tokens_used
                span.estimated_cost_usd = cost_usd
                duration_ms = (span.end_time - span.start_time) * 1000.0
                logger.info(
                    "Trace [%s] finished span '%s' in %.2fms (status=%s, tokens=%d, cost=$%.6f)",
                    span.trace_id,
                    span.name,
                    duration_ms,
                    status,
                    tokens_used,
                    cost_usd,
                )
                break

    def get_trace_summary(self, trace_id: str) -> dict[str, Any]:
        trace_spans = [s for s in self._spans if s.trace_id == trace_id]
        total_tokens = sum(s.tokens_used for s in trace_spans)
        total_cost = sum(s.estimated_cost_usd for s in trace_spans)
        return {
            "trace_id": trace_id,
            "span_count": len(trace_spans),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "components": list({s.component for s in trace_spans}),
        }
