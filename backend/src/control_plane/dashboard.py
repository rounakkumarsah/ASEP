"""
ASEP — Control Plane Dashboard
"""

from src.control_plane.sessions import SessionManager
from src.control_plane.approvals import ApprovalQueue
from src.control_plane.metrics import MetricsDashboard


class DashboardManager:
    """Aggregates high-level state into a single view."""

    def __init__(
        self,
        session_manager: SessionManager,
        approval_queue: ApprovalQueue,
        metrics_dashboard: MetricsDashboard
    ) -> None:
        self.session_manager = session_manager
        self.approval_queue = approval_queue
        self.metrics_dashboard = metrics_dashboard

    def get_system_overview(self) -> dict:
        active_sessions = self.session_manager.list_sessions(status="running")
        pending_approvals = self.approval_queue.list_pending()
        global_metrics = self.metrics_dashboard.get_global_summary()

        return {
            "active_sessions_count": len(active_sessions),
            "pending_approvals_count": len(pending_approvals),
            "metrics": global_metrics,
            "system_status": "healthy"
        }
