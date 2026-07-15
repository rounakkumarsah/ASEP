"""
ASEP — Control Plane Metrics
"""

from src.evaluation.metrics import MetricsCollector, SessionMetrics

class MetricsDashboard:
    """Aggregates performance data system-wide."""

    def __init__(self, metrics_collector: MetricsCollector) -> None:
        self._collector = metrics_collector
        self._sessions: dict[str, SessionMetrics] = {}

    def update_session_metrics(self, session_metrics: SessionMetrics) -> None:
        self._sessions[session_metrics.session_id] = session_metrics

    def get_session_metrics(self, session_id: str) -> SessionMetrics | None:
        return self._sessions.get(session_id)

    def get_global_summary(self) -> dict:
        """Computes system-wide aggregated metrics."""
        sessions = list(self._sessions.values())
        total_sessions = len(sessions)
        if total_sessions == 0:
            return {"total_sessions": 0}

        total_tasks = sum(s.task_count for s in sessions)
        succeeded = sum(s.succeeded for s in sessions)
        failed = sum(s.failed for s in sessions)
        tool_invocations = sum(s.tool_invocations for s in sessions)
        
        avg_latency_ms = sum(s.latency.total_ms for s in sessions) / total_sessions

        return {
            "total_sessions": total_sessions,
            "total_tasks": total_tasks,
            "tasks_succeeded": succeeded,
            "tasks_failed": failed,
            "tool_invocations": tool_invocations,
            "avg_latency_ms": round(avg_latency_ms, 2)
        }
