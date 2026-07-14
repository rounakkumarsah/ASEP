"""
Tests for TaskService
"""

import uuid
import pytest
from unittest.mock import AsyncMock

from src.db.models.task import Task, TaskStatus, TaskType
from src.services.task_service import TaskService, TaskDefinition
from src.services.exceptions import InvalidStateError


@pytest.fixture
def task_service(uow_factory):
    return TaskService(uow_factory)


@pytest.mark.asyncio
async def test_create_tasks_bulk(task_service, mock_uow):
    run_id = uuid.uuid4()
    definitions = [
        TaskDefinition(position=0, title="Task 1", task_type=TaskType.COMMAND, prompt="run 1"),
        TaskDefinition(position=1, title="Task 2", task_type=TaskType.REASONING, prompt="run 2"),
    ]
    
    mock_uow.tasks.create.side_effect = lambda t: t
    
    tasks = await task_service.create_tasks_bulk(run_id, definitions, created_by="user")
    
    assert len(tasks) == 2
    assert tasks[0].position == 0
    assert tasks[1].position == 1
    assert tasks[0].agent_run_id == run_id
    
    assert mock_uow.tasks.create.call_count == 2
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_tasks_bulk_validation(task_service):
    run_id = uuid.uuid4()
    definitions = [
        TaskDefinition(position=0, title="", task_type=TaskType.COMMAND, prompt="run 1"),
    ]
    
    with pytest.raises(ValueError, match="TaskDefinition.title must be non-empty"):
        await task_service.create_tasks_bulk(run_id, definitions)


@pytest.mark.asyncio
async def test_start_task(task_service, mock_uow):
    task_id = uuid.uuid4()
    mock_task = Task(id=task_id, status=TaskStatus.PENDING)
    mock_uow.tasks.get_or_raise.return_value = mock_task
    mock_uow.tasks.update.return_value = Task(id=task_id, status=TaskStatus.RUNNING)
    
    result = await task_service.start_task(task_id)
    
    assert result.status == TaskStatus.RUNNING
    mock_uow.tasks.update.assert_awaited_once_with(mock_task, status=TaskStatus.RUNNING)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_task_invalid_state(task_service, mock_uow):
    task_id = uuid.uuid4()
    mock_task = Task(id=task_id, status=TaskStatus.COMPLETED)
    mock_uow.tasks.get_or_raise.return_value = mock_task
    
    with pytest.raises(InvalidStateError):
        await task_service.start_task(task_id)


@pytest.mark.asyncio
async def test_complete_task(task_service, mock_uow):
    task_id = uuid.uuid4()
    mock_task = Task(id=task_id, status=TaskStatus.RUNNING)
    mock_uow.tasks.get_or_raise.return_value = mock_task
    mock_uow.tasks.update.return_value = Task(id=task_id, status=TaskStatus.COMPLETED)
    
    result = await task_service.complete_task(task_id, result_data={"out": "ok"})
    
    assert result.status == TaskStatus.COMPLETED
    mock_uow.tasks.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
