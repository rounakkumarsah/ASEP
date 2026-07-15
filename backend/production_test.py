import asyncio
from src.production.benchmarking import Benchmarker
from src.production.integration import IntegrationValidator
from src.production.load_testing import LoadTester
from src.production.resilience import CircuitBreaker, CircuitBreakerError
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

async def mock_workload():
    await asyncio.sleep(0.01)

async def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=1.0)
    
    async def failing_task():
        raise ValueError("Simulated failure")
        
    try:
        await breaker.call(failing_task)
    except ValueError:
        pass
        
    try:
        await breaker.call(failing_task)
    except ValueError:
        pass
        
    try:
        await breaker.call(failing_task)
        assert False, "Should raise CircuitBreakerError"
    except CircuitBreakerError:
        print("CircuitBreaker successfully tripped OPEN.")

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

    validator = IntegrationValidator(api)
    report = await validator.validate_e2e()
    assert report["status"] == "PASS", f"E2E failed: {report}"

    print("E2E Integration Validation passed.")
    
    await test_circuit_breaker()
    
    print("Running Load Test (Stress Test)...")
    load_report = await LoadTester.run_stress_test(mock_workload, requests=100, concurrency=10)
    assert load_report["throughput_tps"] > 0
    print(f"Load Test passed with {load_report['throughput_tps']:.2f} TPS")

    print("Integration test passed!")

asyncio.run(run_integration_test())
