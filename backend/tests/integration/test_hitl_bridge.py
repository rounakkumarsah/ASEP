"""
ASEP — Integration Tests for LangGraph ↔ HITL Bridge
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.db.models.hitl_session import HITLSession, HITLStatus
from src.governance.hitl import ApprovalAction, ReviewerRole, get_hitl_engine
from src.runtime import get_langgraph_runtime
from src.unit_of_work.base import AbstractUnitOfWork


class MockUnitOfWork(AbstractUnitOfWork):

    def __init__(self):
        super().__init__()
        self.hitl_sessions = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio
async def test_hitl_bridge_full_lifecycle():
    """Verify enqueuing on pause and resuming on approval works end-to-end."""
    runtime = get_langgraph_runtime()
    engine = get_hitl_engine()

    # Configure mock UOW on the engine
    mock_uow = MockUnitOfWork()
    mock_uow.hitl_sessions.create = AsyncMock(side_effect=lambda x: x)
    engine.uow_factory = lambda: mock_uow

    run_id = str(uuid.uuid4())
    thread_id = "test-thread-hitl-bridge"

    # 1. Start execution run and consume the stream until it pauses (completes stream)
    events = []
    async for event in runtime.execute_run(run_id=run_id, thread_id=thread_id):
        events.append(event)

    # Verify that the graph did run the start and process nodes
    assert any("start" in event for event in events)
    assert any("process" in event for event in events)

    # Verify that the graph state is now paused at the "validate" node
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await runtime.graph.aget_state(config)
    assert snapshot.next == ("validate",)

    # Fetch domain session representation
    # Since we mocked UOW, we construct the session directly for simulation
    db_sessions = mock_uow.hitl_sessions.create.call_args[0][0]
    session = engine._to_domain(db_sessions)
    assert session.decision is None
    assert session.requesting_tool == "human_validation"

    # Mock hitl_sessions get for submit_decision
    db_session_mock = HITLSession(
        session_id=session.session_id,
        execution_id=uuid.UUID(session.execution_id),
        correlation_id=session.correlation_id,
        requesting_agent=session.requesting_agent,
        requesting_tool=session.requesting_tool,
        risk_level=session.risk_level.value,
        status=HITLStatus.PENDING,
        arguments_json=session.modified_arguments,
        justification=session.justification,
        ttl_seconds=300,
    )
    db_session_mock.created_at = datetime.now(timezone.utc)
    mock_uow.hitl_sessions.get = AsyncMock(return_value=db_session_mock)

    # 3. Simulate human approval decision and trigger resumption
    decision_payload = "approve"  # lowercase "approve" matches router expectations
    await engine.submit_decision(
        session_id=session.session_id,
        action=ApprovalAction.APPROVE,
        reviewer="operator_test",
        role=ReviewerRole.OPERATOR,
        notes="Bridge validation test",
    )

    # Invoke runtime resume flow
    resumed_events = []
    async for event in runtime.resume_run(
        thread_id=thread_id, human_input=decision_payload
    ):
        resumed_events.append(event)

    # 4. Verify that execution resumed and reached the end node successfully
    assert len(resumed_events) > 0
    # The last state updates should include the validation node resumption and end node execution
    assert any("validate" in event for event in resumed_events)
    assert any("end" in event for event in resumed_events)

    # Verify final state is completed (next is empty)
    final_snapshot = await runtime.graph.aget_state(config)
    assert not final_snapshot.next
