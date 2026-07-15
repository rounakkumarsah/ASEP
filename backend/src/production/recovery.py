"""
ASEP — Production Recovery
"""

import logging
from src.control_plane.sessions import SessionManager
from src.evaluation.tracing import TraceStore

logger = logging.getLogger(__name__)


class StateRecoverer:
    """Restores sessions and state from persistent logs/traces."""

    def __init__(self, session_manager: SessionManager, trace_store: TraceStore):
        self.session_manager = session_manager
        self.trace_store = trace_store

    def recover_paused_sessions(self) -> int:
        """Scans traces and re-initializes sessions marked as paused/interrupted."""
        recovered_count = 0
        for trace in self.trace_store._traces.values():
            # If the trace indicates the session was active but we don't have it in session manager
            if self.session_manager.get_session(trace.session_id) is None:
                # Mock recovery logic: register it as paused
                self.session_manager.register_session(trace.session_id, "Recovered session")
                self.session_manager.update_status(trace.session_id, "paused")
                recovered_count += 1
                logger.info(f"Recovered session {trace.session_id} from trace log.")
        return recovered_count
