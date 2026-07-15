import asyncio
from src.control_plane.control_api import ControlPlaneAPI
from src.control_plane.sessions import SessionManager
from src.control_plane.agents import AgentManager
from src.control_plane.approvals import ApprovalQueue
from src.control_plane.traces import TraceExplorer
from src.control_plane.metrics import MetricsDashboard
from src.control_plane.policies import PolicyManager
from src.control_plane.audit import AuditExplorer
from src.evaluation.metrics import MetricsCollector
from src.evaluation.tracing import TraceStore
from src.governance.policy_engine import PolicyEvaluator
from src.multi_agent.registry import AgentRegistry
from src.governance.intent import ActionIntent


async def run_integration_test():
    api = ControlPlaneAPI(
        session_manager=SessionManager(),
        agent_manager=AgentManager(AgentRegistry()),
        approval_queue=ApprovalQueue(),
        trace_explorer=TraceExplorer(TraceStore()),
        metrics_dashboard=MetricsDashboard(MetricsCollector()),
        policy_manager=PolicyManager(PolicyEvaluator()),
        audit_explorer=AuditExplorer()
    )

    # Test Session management
    api.sessions.register_session("s1", "Test goal")
    api.pause_session("s1")
    assert api.sessions.get_session("s1").status == "paused"
    api.resume_session("s1")
    assert api.sessions.get_session("s1").status == "running"
    
    # Test Approval queue routing
    intent = ActionIntent(
        session_id="s1", run_id="r1", thread_id="t1", trace_id="trace1",
        actor_role="executor", action_type="deploy", target="prod",
        justification="urgent fix"
    )
    
    # Run the enqueue operation as a background task to simulate governance waiting
    wait_task = asyncio.create_task(api.approvals.enqueue_and_wait(intent))
    
    # Give it a moment to enter the queue
    await asyncio.sleep(0.1)
    
    pending = api.approvals.list_pending()
    assert len(pending) == 1
    
    # Approve it
    api.approve_action(intent.intent_id)
    
    # Wait for the task to finish
    decision = await wait_task
    assert decision.value == "ALLOW"
    
    # Queue should be empty now
    assert len(api.approvals.list_pending()) == 0
    
    # Dashboard summary
    overview = api.dashboard.get_system_overview()
    assert overview["active_sessions_count"] == 1
    assert overview["pending_approvals_count"] == 0

    print("Integration test passed!")

asyncio.run(run_integration_test())
