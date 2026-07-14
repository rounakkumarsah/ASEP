"""
ASEP — Unit of Work Layer
==========================
Public surface of the Phase 0.5 Unit of Work layer.

Re-exports the abstract protocol and the production SQLAlchemy
implementation for a clean, flat import surface::

    from src.unit_of_work import SQLAlchemyUnitOfWork
    from src.unit_of_work import AbstractUnitOfWork  # for type hints / DI

Transaction ownership:
    The Unit of Work is the **sole owner** of ``commit()`` and
    ``rollback()``.  Repositories stage changes via ``flush()`` but never
    end a transaction.

Usage::

    async with SQLAlchemyUnitOfWork() as uow:
        run = AgentRun(goal="Analyse codebase")
        await uow.agent_runs.create(run)
        await uow.commit()
"""

from src.unit_of_work.base import AbstractUnitOfWork
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

__all__ = [
    "AbstractUnitOfWork",
    "SQLAlchemyUnitOfWork",
]
