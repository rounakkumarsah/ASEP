"""
ASEP — Unit Tests for Enterprise Multi-Agent System (Phase P1)
"""

import pytest

from src.multi_agent.coding_agent import CodingAgent
from src.multi_agent.collaboration import SharedStateContext
from src.multi_agent.contracts import AgentRequest, AgentState
from src.multi_agent.debug_agent import DebugAgent
from src.multi_agent.hitl_engine import ApprovalStatus, HITLEngine
from src.multi_agent.message_bus import AgentMessage, AgentMessageBus
from src.multi_agent.review_agent import ReviewAgent
from src.multi_agent.testing_agent import TestingAgent


@pytest.mark.asyncio
async def test_coding_agent_execution():
    agent = CodingAgent()
    req = AgentRequest(
        execution_id="e1",
        correlation_id="c1",
        input_data={"specification": "Create login endpoint", "action": "generate", "language": "python"},
    )
    resp = await agent.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert "def main()" in resp.output_data["generated_code"]


@pytest.mark.asyncio
async def test_review_agent_execution():
    agent = ReviewAgent()
    req = AgentRequest(
        execution_id="e1",
        correlation_id="c1",
        input_data={"code_content": "eval('2+2')"},
    )
    resp = await agent.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert resp.output_data["approved"] is False
    assert len(resp.output_data["issues"]) >= 1


@pytest.mark.asyncio
async def test_testing_agent_execution():
    agent = TestingAgent()
    req = AgentRequest(
        execution_id="e1",
        correlation_id="c1",
        input_data={"target_code": "def add(a, b): return a + b"},
    )
    resp = await agent.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert resp.output_data["passed"] is True


@pytest.mark.asyncio
async def test_debug_agent_execution():
    agent = DebugAgent()
    req = AgentRequest(
        execution_id="e1",
        correlation_id="c1",
        input_data={"error_log": "KeyError: 'user_id'"},
    )
    resp = await agent.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert "Missing expected dictionary key" in resp.output_data["root_cause"]


@pytest.mark.asyncio
async def test_shared_state_context():
    context = SharedStateContext(session_id="s1")
    await context.set("status", "running")
    val = await context.get("status")
    assert val == "running"


@pytest.mark.asyncio
async def test_agent_message_bus():
    bus = AgentMessageBus()
    received = []

    def handler(msg):
        received.append(msg)

    bus.subscribe("task.status", handler)

    msg = AgentMessage(sender_role="coding", recipient_role="supervisor", topic="task.status", payload={"status": "done"})
    await bus.publish(msg)

    assert len(received) == 1
    assert received[0].sender_role == "coding"


def test_hitl_engine_flow():
    hitl = HITLEngine()
    gate = hitl.create_gate("g1", "e1", "code_deploy", {"env": "prod"})

    assert gate.status == ApprovalStatus.PENDING

    updated = hitl.submit_review("g1", approved=True, reviewer_notes="Approved for production")
    assert updated.status == ApprovalStatus.APPROVED

    audit = hitl.get_audit_trail("e1")
    assert len(audit) >= 2
