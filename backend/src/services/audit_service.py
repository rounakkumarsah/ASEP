"""
ASEP — AuditService
=====================
Append-only governance audit log service.

Responsibilities:
    - Validate that required fields (``action``, ``actor_id``) are non-empty.
    - Create immutable ``AuditLog`` entries through the Unit of Work.
    - Expose read-only queries for governance dashboards and distributed
      trace assembly.
    - Commit after every write.

Immutability contract:
    ``AuditLog`` rows are write-once.  This service enforces this by never
    calling ``update`` or ``delete`` on ``AuditLogRepository``.  Only
    ``create`` and read methods are used.  The repository layer provides a
    second defence: ``AuditLogRepository.update()`` and ``.delete()`` raise
    ``NotImplementedError``, and the ORM ``before_update`` event raises
    ``RuntimeError``.

Out of scope for Phase 0.6:
    - PostgreSQL ``BEFORE UPDATE`` trigger (future DB migration).
    - Alerting / PagerDuty webhook integration.
    - Audit log archival / cold storage.

Rules:
    - Never instantiates repositories directly.
    - Never creates or touches ``AsyncSession``.
    - Never calls other services.
    - All database access is via ``AbstractUnitOfWork``.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.db.models.audit_log import (
    ActorType,
    AuditLog,
    AuditOutcome,
    AuditSeverity,
)
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class AuditService:
    """Service owning append-only governance audit log operations.

    All write operations call ``await uow.commit()`` explicitly.
    All read operations open a UoW block for the session but do not commit.

    Args:
        uow_factory: A zero-argument callable returning a fresh
            ``AbstractUnitOfWork``.

    Example::

        service = AuditService(SQLAlchemyUnitOfWork)
        entry = await service.log_event(
            actor_type=ActorType.AGENT,
            actor_id=str(run.id),
            action="agent_run.started",
            resource_type="agent_run",
            outcome=AuditOutcome.SUCCESS,
        )
    """

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        """Initialise with a Unit of Work factory.

        Args:
            uow_factory: Zero-argument callable returning an
                ``AbstractUnitOfWork``.
        """
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------
    # Write — append event
    # ------------------------------------------------------------------

    async def log_event(
        self,
        actor_type: ActorType,
        actor_id: str,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        *,
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_id: str | None = None,
        request_id: uuid.UUID | None = None,
        correlation_id: uuid.UUID | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        log_details: dict[str, Any] | None = None,
        duration_ms: int | None = None,
    ) -> AuditLog:
        """Append a new immutable governance event to the audit log.

        Args:
            actor_type:     Classification of the initiating actor
                            (``SYSTEM``, ``AGENT``, ``USER``).
            actor_id:       Opaque string identifier of the actor.  Must be
                            non-empty (e.g. agent UUID, user ID, service name).
            action:         Dot-namespaced event label (e.g.
                            ``"agent_run.started"``).  Must be non-empty.
            resource_type:  Category of the resource being acted upon
                            (e.g. ``"agent_run"``, ``"task"``).  Must be
                            non-empty.
            outcome:        Result of the operation
                            (``SUCCESS``, ``FAILURE``, ``PARTIAL``,
                            ``UNKNOWN``).
            severity:       Operational severity.  Defaults to ``INFO``.
            resource_id:    Optional opaque identifier of the specific resource
                            instance.  ``None`` for system-level events.
            request_id:     Optional UUID of the originating HTTP request.
            correlation_id: Optional UUID correlating a distributed operation.
            trace_id:       Optional W3C Trace Context trace ID (32 hex chars).
            span_id:        Optional W3C Trace Context span ID (16 hex chars).
            ip_address:     Optional IP address of the initiating client.
            user_agent:     Optional HTTP User-Agent string.
            log_details:    Optional JSONB context (error message, parameters,
                            etc.).
            duration_ms:    Optional duration of the audited operation in
                            milliseconds.

        Returns:
            The persisted, immutable ``AuditLog`` instance.

        Raises:
            ValueError: If ``actor_id``, ``action``, or ``resource_type``
                is empty or whitespace-only.
        """
        actor_id = actor_id.strip()
        if not actor_id:
            raise ValueError("actor_id must be a non-empty string.")
        action = action.strip()
        if not action:
            raise ValueError("action must be a non-empty string.")
        resource_type = resource_type.strip()
        if not resource_type:
            raise ValueError("resource_type must be a non-empty string.")

        entry = AuditLog(
            id=uuid.uuid4(),
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            severity=severity,
            request_id=request_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            ip_address=ip_address,
            user_agent=user_agent,
            log_details=log_details,
            duration_ms=duration_ms,
        )
        async with self._uow_factory() as uow:
            entry = await uow.audit_logs.create(entry)
            await uow.commit()

        logger.debug(
            "AuditLog event written",
            extra={
                "log_id": str(entry.id),
                "action": action,
                "actor_id": actor_id,
                "outcome": outcome.value,
                "severity": severity.value,
            },
        )
        return entry

    # ------------------------------------------------------------------
    # Read — single entry
    # ------------------------------------------------------------------

    async def get_event(self, log_id: uuid.UUID) -> AuditLog:
        """Return a single ``AuditLog`` entry by primary key.

        Args:
            log_id: UUID of the target ``AuditLog`` entry.

        Returns:
            The ``AuditLog`` instance.

        Raises:
            NoResultFound: If no entry with ``log_id`` exists.
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_or_raise(log_id)

    # ------------------------------------------------------------------
    # Read — actor audit trail
    # ------------------------------------------------------------------

    async def get_actor_history(
        self,
        actor_type: ActorType,
        actor_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Return the audit trail for a specific actor.

        Args:
            actor_type: Classification of the actor.
            actor_id:   Opaque actor identifier.
            limit:      Maximum entries to return.
            offset:     Entries to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_by_actor(
                actor_type, actor_id, limit=limit, offset=offset
            )

    # ------------------------------------------------------------------
    # Read — resource audit trail
    # ------------------------------------------------------------------

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Return all audit events targeting a specific resource.

        Args:
            resource_type: Category of the resource.
            resource_id:   Opaque resource instance identifier, or ``None``
                           for system-level events with no specific target.
            limit:         Maximum entries to return.
            offset:        Entries to skip.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_by_resource(
                resource_type, resource_id, limit=limit, offset=offset
            )

    # ------------------------------------------------------------------
    # Read — governance dashboard
    # ------------------------------------------------------------------

    async def get_critical_failures(
        self,
        since: datetime,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Return ``CRITICAL`` severity ``FAILURE`` events since a timestamp.

        Intended for governance dashboards and automated alerting pipelines.

        Args:
            since: Inclusive lower bound for ``created_at`` (timezone-aware
                   UTC ``datetime``).
            limit: Maximum entries to return.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_critical_failures(since, limit=limit)

    # ------------------------------------------------------------------
    # Read — distributed tracing
    # ------------------------------------------------------------------

    async def get_by_correlation(
        self,
        correlation_id: uuid.UUID,
    ) -> list[AuditLog]:
        """Return all log entries sharing a distributed correlation ID.

        Assembles a complete picture of a single distributed operation that
        spanned multiple services or agent hops.

        Args:
            correlation_id: UUID correlating the distributed operation.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at ASC``
            (chronological trace order).
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_by_correlation_id(correlation_id)

    async def get_by_trace(self, trace_id: str) -> list[AuditLog]:
        """Return all log entries belonging to an OpenTelemetry trace.

        Args:
            trace_id: W3C Trace Context trace ID — 32 lowercase hex chars.

        Returns:
            A list of ``AuditLog`` instances ordered by ``created_at ASC``.
        """
        async with self._uow_factory() as uow:
            return await uow.audit_logs.get_by_trace_id(trace_id)
