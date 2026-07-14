"""
ASEP — BaseRepository
======================
Generic async repository base class for SQLAlchemy 2.0.

All domain repositories extend this class and inherit its CRUD primitives.
Repositories are persistence-only: they never call ``session.commit()``,
``session.rollback()``, or ``session.begin()``.  Transaction boundaries are
the responsibility of the caller (future Unit of Work layer).

Design notes:
    - Generic over ``M`` (the ORM model) and ``PK`` (its primary key type,
      always ``uuid.UUID`` in ASEP).
    - ``AsyncSession`` is injected via the constructor so repositories
      participate in the same transaction as their siblings.
    - ``flush`` is used instead of ``commit`` so that pending INSERTs and
      UPDATEs are sent to the DB within the open transaction and become
      visible to subsequent queries in the same session — without ending
      the transaction.
    - All ``list``/query methods accept ``*options`` for caller-supplied
      SQLAlchemy loader strategies (``selectinload``, ``joinedload``,
      ``noload``, etc.).
    - Pagination defaults: ``limit=50``, ``offset=0``, ``max_limit=100``.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.base import ExecutableOption

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

M = TypeVar("M", bound=DeclarativeBase)
PK = TypeVar("PK")

# ---------------------------------------------------------------------------
# Pagination constants
# ---------------------------------------------------------------------------

DEFAULT_LIMIT: int = 50
DEFAULT_OFFSET: int = 0
MAX_LIMIT: int = 100


def _clamp_limit(limit: int) -> int:
    """Clamp ``limit`` to the range ``[1, MAX_LIMIT]``.

    Args:
        limit: Requested page size.

    Returns:
        int: Clamped page size, always in ``[1, 100]``.
    """
    return max(1, min(limit, MAX_LIMIT))


# ---------------------------------------------------------------------------
# BaseRepository
# ---------------------------------------------------------------------------


class BaseRepository(Generic[M, PK]):
    """Generic async repository providing CRUD primitives for an ORM model.

    All domain repositories inherit from this class and extend it with
    model-specific query methods.

    Type parameters:
        M:  The SQLAlchemy ORM model class (e.g. ``AgentRun``).
        PK: The primary-key Python type (always ``uuid.UUID`` in ASEP).

    Attributes:
        _session: The injected ``AsyncSession`` instance.
        _model:   The ORM model class, resolved via ``__orig_class__``
                  at subclass definition time.

    Example::

        async with session_factory() as session:
            repo = AgentRunRepository(session)
            run = await repo.get(some_uuid)
    """

    # Subclasses set this at class body level — see domain repositories.
    _model: type[M]

    def __init__(self, session: AsyncSession) -> None:
        """Initialise the repository with an injected ``AsyncSession``.

        Args:
            session: The SQLAlchemy async session.  The session must be opened
                by the caller; this repository never creates, commits, or
                closes sessions.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Read — single entity
    # ------------------------------------------------------------------

    async def get(
        self,
        pk: PK,
        *options: ExecutableOption,
    ) -> M | None:
        """Retrieve a single entity by primary key.

        Uses ``session.get()`` which hits the identity-map cache before
        issuing a database round-trip, making this the cheapest read path
        for already-loaded entities.

        Args:
            pk:      Primary key value (``uuid.UUID``).
            *options: SQLAlchemy loader strategy options
                      (e.g. ``selectinload``, ``joinedload``, ``noload``).
                      Passed directly to the underlying ``session.get()``
                      call via the ``options`` keyword argument.

        Returns:
            The ORM instance, or ``None`` if no row with ``pk`` exists.
        """
        if options:
            return await self._session.get(self._model, pk, options=list(options))
        return await self._session.get(self._model, pk)

    async def get_or_raise(
        self,
        pk: PK,
        *options: ExecutableOption,
    ) -> M:
        """Retrieve a single entity by primary key or raise ``NoResultFound``.

        Args:
            pk:      Primary key value (``uuid.UUID``).
            *options: SQLAlchemy loader strategy options.

        Returns:
            The ORM instance.

        Raises:
            NoResultFound: If no row with ``pk`` exists in the database.
        """
        instance = await self.get(pk, *options)
        if instance is None:
            raise NoResultFound(
                f"{self._model.__name__} with pk={pk!r} was not found."
            )
        return instance

    # ------------------------------------------------------------------
    # Read — collections
    # ------------------------------------------------------------------

    async def list(
        self,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[M]:
        """Return a paginated list of all entities, ordered by primary key.

        Args:
            *options: SQLAlchemy loader strategy options.
            limit:   Maximum number of rows to return.  Clamped to
                     ``[1, MAX_LIMIT]`` (default ``50``).
            offset:  Number of rows to skip (default ``0``).

        Returns:
            A list of ORM instances.
        """
        stmt = (
            select(self._model)
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Write — create
    # ------------------------------------------------------------------

    async def create(self, instance: M) -> M:
        """Persist a new entity and flush to the database.

        The entity must be fully constructed by the caller before being
        passed here.  ``flush`` makes the INSERT visible within the current
        transaction without committing it.

        Args:
            instance: The ORM instance to persist.

        Returns:
            The same instance, now with any server-side defaults populated
            (e.g. ``created_at``, ``updated_at``).
        """
        self._session.add(instance)
        await self._session.flush([instance])
        await self._session.refresh(instance)
        return instance

    # ------------------------------------------------------------------
    # Write — update
    # ------------------------------------------------------------------

    async def update(self, instance: M, **kwargs: Any) -> M:
        """Apply keyword-argument field updates to an entity and flush.

        Only the fields explicitly passed as ``**kwargs`` are mutated.
        All other fields are left unchanged.

        Args:
            instance: The ORM instance to update.  Must already be tracked
                by ``self._session``.
            **kwargs: Mapping of column attribute name → new value.

        Returns:
            The updated ORM instance, refreshed from the database.

        Raises:
            AttributeError: If a key in ``**kwargs`` is not a valid
                attribute of the model.
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self._session.flush([instance])
        await self._session.refresh(instance)
        return instance

    # ------------------------------------------------------------------
    # Write — delete
    # ------------------------------------------------------------------

    async def delete(self, instance: M) -> None:
        """Delete an entity from the database and flush.

        Args:
            instance: The ORM instance to delete.  Must already be tracked
                by ``self._session``.
        """
        await self._session.delete(instance)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    async def count(self) -> int:
        """Return the total number of rows in the table.

        Returns:
            int: Row count.
        """
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.scalar(stmt)
        return int(result or 0)
