"""
ASEP — Control Plane API Facade
"""

from src.control_plane.agents import AgentManager
from src.control_plane.approvals import ApprovalQueue
from src.control_plane.audit import AuditExplorer
from src.control_plane.dashboard import DashboardManager
from src.control_plane.metrics import MetricsDashboard
from src.control_plane.policies import PolicyManager
from src.control_plane.sessions import SessionManager
from src.control_plane.traces import TraceExplorer
from src.governance.decision import DecisionResult


class ControlPlaneAPI:
    """Unified read/write facade for the Production Control Plane."""

    def __init__(
        self,
        session_manager: SessionManager,
        agent_manager: AgentManager,
        approval_queue: ApprovalQueue,
        trace_explorer: TraceExplorer,
        metrics_dashboard: MetricsDashboard,
        policy_manager: PolicyManager,
        audit_explorer: AuditExplorer,
    ) -> None:
        self.sessions = session_manager
        self.agents = agent_manager
        self.approvals = approval_queue
        self.traces = trace_explorer
        self.metrics = metrics_dashboard
        self.policies = policy_manager
        self.audit = audit_explorer
        self.dashboard = DashboardManager(self.sessions, self.approvals, self.metrics)

    # Write APIs
    def pause_session(self, session_id: str) -> None:
        self.sessions.update_status(session_id, "paused")

    def resume_session(self, session_id: str) -> None:
        self.sessions.update_status(session_id, "running")

    def cancel_session(self, session_id: str) -> None:
        self.sessions.update_status(session_id, "cancelled")

    def approve_action(self, intent_id: str) -> bool:
        return self.approvals.resolve(intent_id, DecisionResult.ALLOW)

    def deny_action(self, intent_id: str) -> bool:
        return self.approvals.resolve(intent_id, DecisionResult.DENY)
