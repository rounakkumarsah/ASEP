"""
ASEP — Control Plane Health Check
"""

import logging

from src.control_plane.agents import AgentManager
from src.control_plane.approvals import ApprovalQueue
from src.control_plane.audit import AuditExplorer
from src.control_plane.control_api import ControlPlaneAPI
from src.control_plane.metrics import MetricsDashboard
from src.control_plane.policies import PolicyManager
from src.control_plane.sessions import SessionManager
from src.control_plane.traces import TraceExplorer
from src.evaluation.metrics import MetricsCollector
from src.evaluation.tracing import TraceStore
from src.governance.policy_engine import PolicyEvaluator
from src.multi_agent.registry import AgentRegistry

logger = logging.getLogger(__name__)


async def control_plane_health_check() -> bool:
    """Verifies that the ControlPlaneAPI integrates its modules correctly."""
    try:
        # Instantiate dependencies
        sessions = SessionManager()
        agents = AgentManager(AgentRegistry())
        approvals = ApprovalQueue()
        traces = TraceExplorer(TraceStore())
        metrics = MetricsDashboard(MetricsCollector())
        policies = PolicyManager(PolicyEvaluator())
        audit = AuditExplorer()

        api = ControlPlaneAPI(
            session_manager=sessions,
            agent_manager=agents,
            approval_queue=approvals,
            trace_explorer=traces,
            metrics_dashboard=metrics,
            policy_manager=policies,
            audit_explorer=audit
        )

        # Basic functional test
        api.sessions.register_session("hc-session", "health check")
        assert len(api.sessions.list_sessions()) == 1

        api.pause_session("hc-session")
        assert api.sessions.get_session("hc-session").status == "paused"

        overview = api.dashboard.get_system_overview()
        assert overview["system_status"] == "healthy"

        logger.info("Control plane health check passed")
        return True
    except Exception as exc:
        logger.warning(f"Control plane health check failed: {exc}")
        return False
