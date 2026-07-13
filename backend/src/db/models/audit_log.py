"""
ASEP — AuditLog ORM Model
==========================
Defines the ``AuditLog`` SQLAlchemy 2.0 mapped class, which provides an
immutable, append-only governance audit trail for every action taken by
any actor (system component, autonomous agent, or human operator) across
the ASEP platform.

Architecture context:
    The ``GovernanceService`` is the sole writer of ``AuditLog`` rows.  No
    other service or agent may INSERT directly.  No actor may UPDATE or DELETE
    any row — the table is conceptually write-once.

    Immutability is enforced at two layers:

    1. **ORM layer** (this file): a ``before_update`` SQLAlchemy mapper event
       raises ``RuntimeError`` if any ORM-level UPDATE is attempted on an
       ``AuditLog`` instance.  This catches accidental mutations inside the
       application before they reach the database.

    2. **Database layer** (future migration): a ``BEFORE UPDATE`` Postgres
       trigger will raise an exception for any SQL-level UPDATE, protecting
       against direct DB access that bypasses the ORM.

    ``TimestampMixin`` is included as required.  ``updated_at`` is present in
    the schema but will physically never be set to a new value — the ORM
    guard prevents it.  This is an accepted trade-off to satisfy the
    TimestampMixin requirement while maintaining immutability semantics.

Design notes:
    - Uses SQLAlchemy 2.0 ``Mapped`` / ``mapped_column`` API throughout;
      the legacy ``Column`` API is intentionally absent.
    - ``ActorType``, ``AuditSeverity``, and ``AuditOutcome`` are stored as
      native Postgres ``ENUM`` types for DB-level constraint enforcement.
    - ``actor_id`` and ``resource_id`` are ``String(255)`` — not UUIDs or FKs.
      Audit records must outlive all other records; FK constraints would make
      it impossible to delete runs, tasks, or users without first purging
      their audit history, which defeats the purpose of an audit log.
    - ``resource_id`` is nullable to accommodate system-level events that
      do not target a specific resource (e.g. ``SYSTEM_STARTUP``,
      ``POLICY_RELOAD``).
    - ``ip_address`` is ``String(45)`` — covers IPv4 (max 15 chars), IPv6
      (max 39 chars), and IPv4-mapped IPv6 (max 45 chars) without requiring
      the ``postgresql.INET`` dialect type.
    - ``request_id`` and ``correlation_id`` are UUIDs — typed for HTTP
      request tracing and distributed fan-out tracing, respectively.
    - ``trace_id`` (``String(64)``) and ``span_id`` (``String(64)``) carry
      OpenTelemetry W3C Trace Context identifiers: trace IDs are 32 hex
      chars (128-bit) and span IDs are 16 hex chars (64-bit).  Both are
      stored as strings to remain compatible with any OTel SDK or propagation
      format without type conversion.
    - ``duration_ms`` records how long the audited operation took, enabling
      SLA and performance governance queries without joining to external
      telemetry stores.
    - The JSONB ``metadata`` column is mapped to the Python attribute
      ``log_details`` to avoid shadowing SQLAlchemy's reserved
      ``DeclarativeBase.metadata`` attribute.  It is aliased to the Postgres
      column ``metadata`` via the positional name argument in
      ``mapped_column("metadata", JSONB, ...)``.
    - No SQLAlchemy relationships are declared.  All ID fields are opaque
      references; cross-table joins are performed by the ``GovernanceService``
      at query time.
    - All timestamps are timezone-aware (``TIMESTAMPTZ``).  Server-side
      defaults via ``func.now()`` are used — not Python-side
      ``datetime.utcnow()`` (deprecated in Python 3.12).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


# ---------------------------------------------------------------------------
# ActorType
# ---------------------------------------------------------------------------


class ActorType(str, enum.Enum):
    """Classification of the entity that initiated an audited action.

    Inheriting from ``str`` means every member is simultaneously a plain
    Python string and an enum member, which simplifies JSON serialisation
    and direct string comparison without requiring ``.value`` access.

    Attributes:
        SYSTEM: An internal platform component acting autonomously — a
            lifecycle hook, background scheduler, policy engine, or
            infrastructure service.  There is no human in the loop.
        AGENT: An autonomous AI agent — the Planner, Supervisor, or any
            worker agent dispatched by the ``ExecutionEngine``.
        USER: A human operator interacting with the platform via the REST
            API, the frontend UI, or an authenticated CLI session.
    """

    SYSTEM = "system"
    AGENT = "agent"
    USER = "user"


# ---------------------------------------------------------------------------
# AuditSeverity
# ---------------------------------------------------------------------------


class AuditSeverity(str, enum.Enum):
    """Operational severity of an audited event.

    Mirrors Python's ``logging`` module levels for operational familiarity.
    The ``GovernanceService`` selects the appropriate severity at log time;
    alerting rules and dashboard thresholds are calibrated against these
    values.

    Attributes:
        DEBUG: Trace-level event; high volume and low operational signal.
            Typically disabled in production unless actively debugging.
        INFO: Normal operational event — an agent started, a task completed,
            a user authenticated successfully.
        WARNING: Potentially problematic event that did not cause a failure
            but warrants attention (e.g. retry triggered, rate limit
            approached).
        ERROR: A handled error — the operation may have partially succeeded
            but at least one component failed.  Requires investigation.
        CRITICAL: A severe, system-level event requiring immediate human
            response — policy violation, data integrity breach, executor
            crash.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# AuditOutcome
# ---------------------------------------------------------------------------


class AuditOutcome(str, enum.Enum):
    """Result of the operation recorded by an ``AuditLog`` entry.

    Attributes:
        SUCCESS: The operation completed exactly as intended.  All
            postconditions were satisfied.
        FAILURE: The operation failed.  ``log_details`` carries the error
            context, exception type, and traceback summary.
        PARTIAL: The operation completed partially — some postconditions were
            satisfied and others were not.  Common for batch or fan-out
            operations where individual items may succeed or fail
            independently.
        UNKNOWN: The outcome cannot be determined at log time — typically
            used for fire-and-forget operations or when the response has not
            yet been received.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------


class AuditLog(TimestampMixin, Base):
    """ORM representation of a single immutable governance audit log entry.

    Each row records one audited event: who acted, on what, with what
    outcome, and in what distributed tracing context.  Rows are written
    once by the ``GovernanceService`` and must never be modified or deleted.

    Table:
        audit_logs

    Primary key:
        ``id`` — UUID v4, generated application-side so the caller can hold
        the identifier before the INSERT is committed (useful for
        correlation with external systems).

    Immutability:
        A ``before_update`` SQLAlchemy mapper event (registered below the
        class definition) raises ``RuntimeError`` if any ORM-level UPDATE is
        attempted.  A DB-level trigger enforcement will be added in a
        dedicated migration.

    Relationships:
        None — all IDs are opaque references.  The ``GovernanceService``
        performs cross-table joins at query time.

    Attributes:
        id: UUID v4 primary key, generated application-side before INSERT.
        actor_type: Classification of the entity that initiated the action.
            Stored as a native Postgres ``ENUM``.
        actor_id: Opaque string identifier for the actor — a UUID string for
            agents and users, a label such as ``"system"`` or
            ``"scheduler"`` for system components.  ``String(255)``; no FK
            constraint so audit records outlive the entities they reference.
        action: Short, dot-namespaced label for the audited operation
            (e.g. ``"agent_run.created"``, ``"task.failed"``,
            ``"policy.violated"``).  Non-nullable; must not be empty
            (``ck_audit_log_action_not_empty``).
        resource_type: Category of the resource affected by the action
            (e.g. ``"agent_run"``, ``"task"``, ``"memory_entry"``,
            ``"policy"``).  Non-nullable; acts as a namespace for
            ``resource_id``.
        resource_id: Opaque identifier of the specific resource instance.
            Nullable — system-level events that do not target a specific
            resource (e.g. ``SYSTEM_STARTUP``) set this to ``None``.
        severity: Operational severity of this event.  Defaults to
            ``AuditSeverity.INFO``.
        outcome: Result of the audited operation.  Non-nullable; must be
            set explicitly by the ``GovernanceService`` at log time.
        request_id: UUID of the originating HTTP request.  ``None`` for
            background tasks and scheduled operations that do not originate
            from an HTTP request.
        correlation_id: UUID used to correlate all log entries that belong
            to a single distributed operation spanning multiple services or
            agent hops.  ``None`` if no correlation context was propagated.
        trace_id: OpenTelemetry W3C Trace Context trace identifier —
            32 lowercase hex characters (128-bit).  ``None`` if OTel
            instrumentation was not active for this operation.
        span_id: OpenTelemetry W3C Trace Context span identifier —
            16 lowercase hex characters (64-bit) identifying the specific
            span within ``trace_id``.  ``None`` if OTel instrumentation was
            not active.
        ip_address: IPv4 or IPv6 address of the originating client.
            ``String(45)`` — covers IPv4 (max 15 chars), IPv6 (max 39 chars),
            and IPv4-mapped IPv6 (max 45 chars).  ``None`` for system-
            initiated or background operations.
        user_agent: HTTP ``User-Agent`` header string from the originating
            request.  ``None`` for non-HTTP-originated operations.
        log_details: Arbitrary JSONB payload carrying operation-specific
            context — error messages, diff snapshots, policy rule IDs,
            token counts, etc.  Stored in the Postgres column ``metadata``;
            mapped to ``log_details`` in Python to avoid shadowing
            ``DeclarativeBase.metadata``.
        duration_ms: Wall-clock duration of the audited operation in
            milliseconds.  ``None`` if not measured.  Used for SLA and
            performance governance queries.
        created_at: Inherited from ``TimestampMixin``.  Set once on INSERT;
            effectively the event timestamp.
        updated_at: Inherited from ``TimestampMixin``.  Present in the
            schema but physically never updated — the ORM immutability guard
            prevents it.
    """

    __tablename__ = "audit_logs"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side before INSERT.",
    )

    # ------------------------------------------------------------------
    # Actor
    # ------------------------------------------------------------------

    actor_type: Mapped[ActorType] = mapped_column(
        Enum(
            ActorType,
            name="actor_type",           # Postgres ENUM type name
            native_enum=True,            # Use a real Postgres ENUM (not VARCHAR)
            create_constraint=True,      # Emit CREATE TYPE on DDL generation
            validate_strings=True,       # Reject unknown values on load
        ),
        nullable=False,
        doc="Classification of the entity that initiated the action.",
    )

    actor_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc=(
            "Opaque string identifier for the actor — a UUID string for agents "
            "and users, or a label such as 'system' for platform components.  "
            "String(255); no FK so audit records outlive the entities they reference.  "
            "Constrained non-empty by ck_audit_log_actor_id_not_empty."
        ),
    )

    # ------------------------------------------------------------------
    # Action and resource
    # ------------------------------------------------------------------

    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc=(
            "Short, dot-namespaced label for the audited operation "
            "(e.g. 'agent_run.created', 'task.failed', 'policy.violated').  "
            "Constrained non-empty by ck_audit_log_action_not_empty."
        ),
    )

    resource_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc=(
            "Category of the resource affected by the action "
            "(e.g. 'agent_run', 'task', 'memory_entry', 'policy').  "
            "Acts as a namespace for resource_id."
        ),
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc=(
            "Opaque identifier of the specific resource instance.  "
            "Nullable — system-level events (SYSTEM_STARTUP, POLICY_RELOAD) "
            "that do not target a specific resource set this to None."
        ),
    )

    # ------------------------------------------------------------------
    # Severity and outcome
    # ------------------------------------------------------------------

    severity: Mapped[AuditSeverity] = mapped_column(
        Enum(
            AuditSeverity,
            name="audit_severity",       # Postgres ENUM type name
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=AuditSeverity.INFO,
        doc="Operational severity of this event.  Defaults to INFO.",
    )

    outcome: Mapped[AuditOutcome] = mapped_column(
        Enum(
            AuditOutcome,
            name="audit_outcome",        # Postgres ENUM type name
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        doc=(
            "Result of the audited operation.  "
            "Must be set explicitly by the GovernanceService at log time."
        ),
    )

    # ------------------------------------------------------------------
    # Request / distributed trace context
    # ------------------------------------------------------------------

    request_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        doc=(
            "UUID of the originating HTTP request.  "
            "None for background tasks and scheduled operations."
        ),
    )

    correlation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        doc=(
            "UUID correlating all log entries for a single distributed operation "
            "spanning multiple services or agent hops.  "
            "None if no correlation context was propagated."
        ),
    )

    trace_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc=(
            "OpenTelemetry W3C Trace Context trace identifier — "
            "32 lowercase hex characters (128-bit).  "
            "None if OTel instrumentation was not active for this operation."
        ),
    )

    span_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc=(
            "OpenTelemetry W3C Trace Context span identifier — "
            "16 lowercase hex characters (64-bit) within trace_id.  "
            "None if OTel instrumentation was not active."
        ),
    )

    # ------------------------------------------------------------------
    # Client context
    # ------------------------------------------------------------------

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc=(
            "IPv4 or IPv6 address of the originating client.  "
            "String(45) covers IPv4 (≤15 chars), IPv6 (≤39 chars), "
            "and IPv4-mapped IPv6 (≤45 chars).  "
            "None for system-initiated or background operations."
        ),
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "HTTP User-Agent header string from the originating request.  "
            "None for non-HTTP-originated operations."
        ),
    )

    # ------------------------------------------------------------------
    # Operation payload (JSONB)
    # ------------------------------------------------------------------

    log_details: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",                      # Postgres column name — avoids Base.metadata clash
        JSONB,
        nullable=True,
        doc=(
            "Arbitrary JSONB payload carrying operation-specific context — "
            "error messages, diff snapshots, policy rule IDs, token counts, etc.  "
            "Stored in the Postgres column 'metadata'; mapped to 'log_details' "
            "in Python to avoid shadowing DeclarativeBase.metadata."
        ),
    )

    # ------------------------------------------------------------------
    # Performance telemetry
    # ------------------------------------------------------------------

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc=(
            "Wall-clock duration of the audited operation in milliseconds.  "
            "None if not measured.  "
            "Used for SLA and performance governance queries."
        ),
    )

    # ------------------------------------------------------------------
    # Check constraints and indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Check constraints -------------------------------------------------

        # Actor ID must not be a blank string
        CheckConstraint(
            "actor_id <> ''",
            name="ck_audit_log_actor_id_not_empty",
        ),

        # Action label must not be a blank string
        CheckConstraint(
            "action <> ''",
            name="ck_audit_log_action_not_empty",
        ),

        # Indexes -----------------------------------------------------------

        # Composite: "What did this actor do?" — primary audit query
        Index("ix_audit_log_actor", "actor_type", "actor_id"),

        # Composite: "What happened to this resource?"
        Index("ix_audit_log_resource", "resource_type", "resource_id"),

        # Single-column: filter by action type
        Index("ix_audit_log_action", "action"),

        # Single-column: severity-based alerting and dashboards
        Index("ix_audit_log_severity", "severity"),

        # Single-column: failure analysis
        Index("ix_audit_log_outcome", "outcome"),

        # Single-column: trace all events for a single HTTP request
        Index("ix_audit_log_request_id", "request_id"),

        # Single-column: trace a distributed request chain
        Index("ix_audit_log_correlation_id", "correlation_id"),

        # Single-column: look up by OTel trace ID
        Index("ix_audit_log_trace_id", "trace_id"),

        # Single-column: time-range queries and cursor-based pagination
        Index("ix_audit_log_created_at", "created_at"),

        # Composite: "Show all CRITICAL FAILUREs in the last hour"
        Index(
            "ix_audit_log_severity_outcome_created_at",
            "severity",
            "outcome",
            "created_at",
        ),

        # Composite: actor history, time-ordered — "All actions by agent X"
        Index(
            "ix_audit_log_actor_created_at",
            "actor_type",
            "actor_id",
            "created_at",
        ),
    )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation.

        Returns:
            str: A string of the form
                ``AuditLog(id=..., actor_type=..., action=...,
                severity=..., outcome=...)``.
        """
        return (
            f"AuditLog("
            f"id={self.id!s}, "
            f"actor_type={self.actor_type!r}, "
            f"action={self.action!r}, "
            f"severity={self.severity!r}, "
            f"outcome={self.outcome!r}"
            f")"
        )


# ---------------------------------------------------------------------------
# Immutability guard — ORM layer
# ---------------------------------------------------------------------------


@event.listens_for(AuditLog, "before_update")
def _prevent_audit_log_update(mapper: Any, connection: Any, target: AuditLog) -> None:
    """Raise ``RuntimeError`` on any ORM-level UPDATE attempt.

    ``AuditLog`` rows are immutable by design.  This event listener fires
    before SQLAlchemy's unit of work flushes a dirty ``AuditLog`` instance
    to the database, intercepting the UPDATE before it reaches the wire.

    Direct SQL ``UPDATE`` statements (via ``connection.execute()``) bypass
    the ORM event system and are handled separately by a DB-level trigger
    added in a dedicated migration.

    Args:
        mapper: The SQLAlchemy ``Mapper`` instance for ``AuditLog``.
        connection: The ``Connection`` being used for the flush.
        target: The ``AuditLog`` instance that was marked dirty.

    Raises:
        RuntimeError: Always.  Includes the ``id`` of the offending row
            so the caller can trace the mutation back to its origin.
    """
    raise RuntimeError(
        f"AuditLog rows are immutable and must never be updated after INSERT.  "
        f"Attempted ORM UPDATE on AuditLog(id={target.id!s}).  "
        f"To amend a record, create a new AuditLog entry with corrected data "
        f"and reference the original id in log_details."
    )
