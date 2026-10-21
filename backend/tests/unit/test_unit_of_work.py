import pytest
from unittest.mock import AsyncMock, MagicMock
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


@pytest.fixture
def mock_session_factory():
    """Fixture providing a mock async session factory."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()

    factory = MagicMock(return_value=session)
    return factory, session


@pytest.mark.asyncio
async def test_uow_session_accessible_in_context(mock_session_factory):
    factory, mock_session = mock_session_factory
    uow = SQLAlchemyUnitOfWork(session_factory=factory)

    async with uow:
        assert uow.session is mock_session
        assert uow.db_session is mock_session
        assert uow._session is mock_session


@pytest.mark.asyncio
async def test_uow_session_outside_context_raises():
    uow = SQLAlchemyUnitOfWork(session_factory=MagicMock())

    with pytest.raises(RuntimeError, match="SQLAlchemyUnitOfWork.session accessed outside an active"):
        _ = uow.session

    with pytest.raises(RuntimeError, match="SQLAlchemyUnitOfWork.session accessed outside an active"):
        _ = uow.db_session


@pytest.mark.asyncio
async def test_uow_repositories_instantiation(mock_session_factory):
    factory, mock_session = mock_session_factory
    uow = SQLAlchemyUnitOfWork(session_factory=factory)

    async with uow:
        assert uow.agent_runs is not None
        assert uow.tasks is not None
        assert uow.memory_entries is not None
        assert uow.audit_logs is not None
        assert uow.knowledge_documents is not None
        assert uow.users is not None
        assert uow.hitl_sessions is not None


@pytest.mark.asyncio
async def test_uow_commit_and_rollback(mock_session_factory):
    factory, mock_session = mock_session_factory
    uow = SQLAlchemyUnitOfWork(session_factory=factory)

    async with uow:
        await uow.commit()
        mock_session.commit.assert_awaited_once()

        await uow.rollback()
        mock_session.rollback.assert_awaited_once()

    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_uow_commit_outside_context_raises():
    uow = SQLAlchemyUnitOfWork(session_factory=MagicMock())

    with pytest.raises(RuntimeError, match="SQLAlchemyUnitOfWork.commit\\(\\) called outside an active"):
        await uow.commit()

    with pytest.raises(RuntimeError, match="SQLAlchemyUnitOfWork.rollback\\(\\) called outside an active"):
        await uow.rollback()


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(mock_session_factory):
    factory, mock_session = mock_session_factory
    uow = SQLAlchemyUnitOfWork(session_factory=factory)

    class CustomTestException(Exception):
        pass

    with pytest.raises(CustomTestException):
        async with uow:
            raise CustomTestException("Something went wrong")

    mock_session.rollback.assert_awaited_once()
    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_project_context_retrieval_pattern(mock_session_factory):
    """Simulates active project retrieval in conversations.py to verify no AttributeError."""
    factory, mock_session = mock_session_factory
    mock_result = MagicMock()
    mock_project = MagicMock(id="proj-123")
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_result

    uow = SQLAlchemyUnitOfWork(session_factory=factory)
    resolved_project_id = None

    async with uow:
        stmt = "SELECT * FROM projects WHERE org_id = 'org-1' AND is_active = true"
        res = await uow.session.execute(stmt)
        proj = res.scalar_one_or_none()
        if proj:
            resolved_project_id = str(proj.id)

    assert resolved_project_id == "proj-123"
