"""
Tests for AgentRunService
"""

import uuid
import pytest
from unittest.mock import AsyncMock

from src.db.models.agent_run import AgentRun, RunStatus
from src.services.agent_run_service import AgentRunService
from src.services.exceptions import InvalidStateError


@pytest.fixture
def agent_run_service(uow_factory):
    return AgentRunService(uow_factory)


def test_init(agent_run_service, mock_uow):
    assert agent_run_service._uow_factory() is mock_uow


@pytest.mark.asyncio
async def test_create_run(agent_run_service, mock_uow):
    # Setup
    run_id = uuid.uuid4()
    mock_run = AgentRun(id=run_id, status=RunStatus.PENDING)
    mock_uow.agent_runs.create.return_value = mock_run

    # Execute
    result = await agent_run_service.create_run(
        goal="Test goal",
        plan={"steps": []},
        created_by="test_user"
    )

    # Assert
    assert result.id == run_id
    mock_uow.agent_runs.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_run_validation(agent_run_service):
    with pytest.raises(ValueError, match="AgentRun.goal must be non-empty"):
        await agent_run_service.create_run(goal="   ")


@pytest.mark.asyncio
async def test_start_run_success(agent_run_service, mock_uow):
    # Setup
    run_id = uuid.uuid4()
    mock_run = AgentRun(id=run_id, status=RunStatus.PENDING)
    mock_uow.agent_runs.get_or_raise.return_value = mock_run
    mock_run_updated = AgentRun(id=run_id, status=RunStatus.RUNNING)
    mock_uow.agent_runs.update.return_value = mock_run_updated

    # Execute
    result = await agent_run_service.start_run(run_id)

    # Assert
    assert result.status == RunStatus.RUNNING
    mock_uow.agent_runs.update.assert_awaited_once_with(mock_run, status=RunStatus.RUNNING)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_run_invalid_state(agent_run_service, mock_uow):
    # Setup
    run_id = uuid.uuid4()
    # Already RUNNING
    mock_run = AgentRun(id=run_id, status=RunStatus.RUNNING)
    mock_uow.agent_runs.get_or_raise.return_value = mock_run

    # Execute & Assert
    with pytest.raises(InvalidStateError):
        await agent_run_service.start_run(run_id)


@pytest.mark.asyncio
async def test_complete_run(agent_run_service, mock_uow):
    run_id = uuid.uuid4()
    mock_run = AgentRun(id=run_id, status=RunStatus.RUNNING)
    mock_uow.agent_runs.get_or_raise.return_value = mock_run
    mock_run_updated = AgentRun(id=run_id, status=RunStatus.COMPLETED)
    mock_uow.agent_runs.update.return_value = mock_run_updated

    result = await agent_run_service.complete_run(run_id, result_data={"success": True})

    assert result.status == RunStatus.COMPLETED
    mock_uow.agent_runs.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
