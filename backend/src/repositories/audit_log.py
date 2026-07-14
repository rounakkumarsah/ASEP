"""
ASEP — AuditLogRepository
===========================
Async repository for the ``AuditLog`` ORM model.

Extends ``BaseRepository`` with domain-specific query methods scoped to the
``audit_logs`` table.  All methods leverage the composite and single-column
indexes declared on the model and never call ``session.commit()``,
``session.rollback()``, or ``session.begin()``.

Immutability contract:
    ``AuditLog`` rows are write-once.  This repository enforces immutability
    at the repository layer — ``update()`` and ``delete()`` are overridden to
    raise ``NotImplementedError`` immediately, before the ORM ``before_update``
    event listener fires.  This provides a clear, early failure at the
    call-site rather than a cryptic SQLAlchemy event error.

    Only ``create()`` is permitted.

Query hot-paths covered:
    - Actor audit trail: ``get_by_actor``
    - Resource audit trail: ``get_by_resource``
    - Action namespace filter: ``get_by_action``
    - Severity-based alerting: ``get_by_severity``
    - Failure analysis: ``get_by_outcome``
    - Distributed tracing: ``get_by_correlation_id``, ``get_by_request_id``, ``get_by_trace_id``
    - Governance dashboard: ``get_critical_failures``
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from src.db.models.audit_log import ActorType, AuditLog, AuditOutcome, AuditSeverity
from src.repositories.base import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    BaseRepository,
    _clamp_limit,
)


class AuditLogRepository(BaseRepository[AuditLog, uuid.UUID]):
    """Async repository for ``AuditLog`` persistence and governance queries.

    Inherits CRUD primitives from ``BaseRepository``, but **overrides**
    ``update()`` and ``delete()`` to raise ``NotImplementedError`` because
    ``AuditLog`` rows are immutable by design.

    Only ``create()`` and read operations are permitted.

    Adds query methods that map directly to the indexes on ``audit_logs``:

    - ``ix_audit_log_actor``
    - ``ix_audit_log_resource``
    - ``ix_audit_log_action``
    - ``ix_audit_log_severity``
    - ``ix_audit_log_outcome``
    - ``ix_audit_log_request_id``
    - ``ix_audit_log_correlation_id``
    - ``ix_audit_log_trace_id``
    - ``ix_audit_log_created_at``
    - ``ix_audit_log_severity_outcome_created_at``
    - ``ix_audit_log_actor_created_at``

    Attributes:
        _model: Bound to ``AuditLog``.

    Example::

        repo = AuditLogRepository(session)
        failures = await repo.get_critical_failures(since=one_hour_ago)
    """

    _model = AuditLog

    # ------------------------------------------------------------------
    # Immutability guards — override BaseRepository mutators
    # ------------------------------------------------------------------

    async def update(self, instance: AuditLog, **kwargs: Any) -> AuditLog:  # type: ignore[override]
        """Raise ``NotImplementedError`` — ``AuditLog`` rows are immutable.

        ``AuditLog`` rows are write-once.  To amend a record, create a new
        ``AuditLog`` entry with corrected data and reference the original
        ``id`` in ``log_details``.

        Args:
            instance: Ignored.
            **kwargs: Ignored.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "AuditLog rows are immutable and must never be updated after INSERT.  "
            "Create a new AuditLog entry with corrected data and reference the "
            "original id in log_details."
        )

    async def delete(self, instance: AuditLog) -> None:  # type: ignore[override]
        """Raise ``NotImplementedError`` — ``AuditLog`` rows cannot be deleted.

        Audit log entries form the permanent governance record of the
        platform.  Deletion is prohibited at every layer.

        Args:
            instance: Ignored.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "AuditLog rows are immutable and must never be deleted.  "
            "Implement a data-retention archive strategy if old entries must "
            "be removed from the primary table."
        )

    # ------------------------------------------------------------------
    # Actor audit trail
    # ------------------------------------------------------------------

    async def get_by_actor(
        self,
        actor_type: ActorType,
        actor_id: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AuditLog]:
        """Return audit log entries for a specific actor, newest first.

        Uses the composite index ``ix_audit_log_actor_created_at``.

        Args:
            actor_type: Classification of the actor
                        (``SYSTEM``, ``AGENT``, ``USER``).
            actor_id:   Opaque actor identifier string.
            *options:   SQLAlchemy loader strategy options.
            limit:      Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:     Rows to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.actor_type == actor_type,
                AuditLog.actor_id == actor_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Resource audit trail
    # ------------------------------------------------------------------

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str | None,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AuditLog]:
        """Return audit log entries targeting a specific resource.

        Uses ``ix_audit_log_resource``.  Pass ``resource_id=None`` to
        retrieve all system-level events for a ``resource_type`` that
        lack a specific resource identifier.

        Args:
            resource_type: Category of the resource
                           (e.g. ``"agent_run"``, ``"task"``).
            resource_id:   Opaque resource instance identifier, or ``None``
                           for system-level events.
            *options:      SQLAlchemy loader strategy options.
            limit:         Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:        Rows to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        stmt = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(_clamp_limit(limit)).offset(offset)
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Action namespace filter
    # ------------------------------------------------------------------

    async def get_by_action(
        self,
        action: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AuditLog]:
        """Return audit log entries for a given action label.

        Uses ``ix_audit_log_action``.  Action labels follow the convention
        ``"<resource_type>.<event>"`` (e.g. ``"agent_run.created"``).

        Args:
            action:   Dot-namespaced action label.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Severity-based alerting
    # ------------------------------------------------------------------

    async def get_by_severity(
        self,
        severity: AuditSeverity,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AuditLog]:
        """Return audit log entries at or above a severity level.

        Uses ``ix_audit_log_severity``.

        Args:
            severity: The ``AuditSeverity`` value to filter on.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.severity == severity)
            .order_by(AuditLog.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Outcome / failure analysis
    # ------------------------------------------------------------------

    async def get_by_outcome(
        self,
        outcome: AuditOutcome,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AuditLog]:
        """Return audit log entries with a given outcome.

        Uses ``ix_audit_log_outcome``.

        Args:
            outcome:  The ``AuditOutcome`` value to filter on.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.outcome == outcome)
            .order_by(AuditLog.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Distributed tracing
    # ------------------------------------------------------------------

    async def get_by_correlation_id(
        self,
        correlation_id: uuid.UUID,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AuditLog]:
        """Return all log entries sharing a distributed correlation ID.

        Uses ``ix_audit_log_correlation_id``.  Assembles a complete picture
        of a single distributed operation that spanned multiple services or
        agent hops.

        Args:
            correlation_id: UUID correlating the distributed operation.
            *options:       SQLAlchemy loader strategy options.
            limit:          Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at ASC``
            (chronological, for trace reconstruction).
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.correlation_id == correlation_id)
            .order_by(AuditLog.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_request_id(
        self,
        request_id: uuid.UUID,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AuditLog]:
        """Return all log entries for a single HTTP request.

        Uses ``ix_audit_log_request_id``.

        Args:
            request_id: UUID of the originating HTTP request.
            *options:   SQLAlchemy loader strategy options.
            limit:      Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at ASC``.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.request_id == request_id)
            .order_by(AuditLog.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_trace_id(
        self,
        trace_id: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AuditLog]:
        """Return all log entries belonging to an OpenTelemetry trace.

        Uses ``ix_audit_log_trace_id``.

        Args:
            trace_id: W3C Trace Context trace identifier — 32 lowercase
                      hex characters (128-bit).
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at ASC``
            (chronological span order).
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.trace_id == trace_id)
            .order_by(AuditLog.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Governance dashboard
    # ------------------------------------------------------------------

    async def get_critical_failures(
        self,
        since: datetime,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AuditLog]:
        """Return ``CRITICAL`` severity ``FAILURE`` entries since a timestamp.

        Uses the composite index ``ix_audit_log_severity_outcome_created_at``
        which covers all three filter columns without a full table scan.
        Intended for governance dashboards and alerting pipelines.

        Args:
            since:    Inclusive lower bound for ``created_at`` (timezone-aware
                      UTC datetime).
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``
            (most recent critical failure first).
        """
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.severity == AuditSeverity.CRITICAL,
                AuditLog.outcome == AuditOutcome.FAILURE,
                AuditLog.created_at >= since,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())
