"""
ASEP — OpenTelemetry & Distributed Tracing Integration
=======================================================
Provides OpenTelemetry compatible span creation, correlation ID injection,
structured logging propagation, and Prometheus metrics export.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OpenTelemetryProvider:
    """OpenTelemetry tracing context and metric exporter wrapper."""

    def __init__(self, service_name: str = "asep-backend") -> None:
        self.service_name = service_name

    def create_correlation_id(self) -> str:
        return f"trace-{uuid.uuid4().hex[:16]}"

    def inject_context(self, correlation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload_copy = dict(payload)
        payload_copy["trace_id"] = correlation_id
        payload_copy["service_name"] = self.service_name
        return payload_copy

    def export_prometheus_metrics(self, metrics_data: Dict[str, Any]) -> str:
        lines = []
        for key, value in metrics_data.items():
            metric_name = f"asep_{key.lower()}"
            if isinstance(value, (int, float)):
                lines.append(f"# HELP {metric_name} Metric for {key}")
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name} {value}")
        return "\n".join(lines)
