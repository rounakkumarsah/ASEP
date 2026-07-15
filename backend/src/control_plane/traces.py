"""
ASEP — Control Plane Traces
"""

from src.evaluation.tracing import TraceStore, Trace

class TraceExplorer:
    """Read-only view over the global TraceStore for deep execution visibility."""

    def __init__(self, trace_store: TraceStore) -> None:
        self._store = trace_store

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._store.get(trace_id)

    def list_traces(self, session_id: str | None = None, run_id: str | None = None) -> list[Trace]:
        traces = []
        # In a real database we would query; here we filter the in-memory store
        for trace in self._store._traces.values():
            if session_id and trace.session_id != session_id:
                continue
            if run_id and trace.run_id != run_id:
                continue
            traces.append(trace)
        return traces
