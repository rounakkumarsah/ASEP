"""
ASEP — Service Layer Exceptions
=================================
Shared exception types for the Phase 0.6 Service Layer.

These exceptions represent business-rule violations — not data-access errors.
Data-access errors (``NoResultFound``, SQLAlchemy exceptions) propagate
unchanged from the repository layer; services never swallow them.

Design notes:
    - ``InvalidStateError`` inherits from ``ValueError`` so that broad
      ``except ValueError`` clauses catch it without special casing.
    - Structured fields (``entity_type``, ``entity_id``, ``current_status``,
      ``attempted_transition``) enable structured logging in the API layer
      without string parsing.
"""

from __future__ import annotations

import uuid


class InvalidStateError(ValueError):
    """Raised when a service method attempts an illegal state transition.

    Inherits from ``ValueError`` so it is caught by ``except ValueError``
    clauses without requiring special handling.

    Attributes:
        entity_type:          Human-readable name of the ORM entity class
                              (e.g. ``"AgentRun"``, ``"Task"``).
        entity_id:            UUID primary key of the offending entity.
        current_status:       The entity's current status at the time of the
                              attempted transition.
        attempted_transition: Description of the transition that was refused
                              (e.g. ``"start"`` or ``"complete"``).

    Example::

        raise InvalidStateError(
            entity_type="AgentRun",
            entity_id=run.id,
            current_status=run.status.value,
            attempted_transition="start",
        )
    """

    def __init__(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        current_status: str,
        attempted_transition: str,
    ) -> None:
        """Initialise with structured transition context.

        Args:
            entity_type:          Name of the entity class.
            entity_id:            UUID primary key of the entity.
            current_status:       Current status value as a string.
            attempted_transition: Label of the refused transition.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.current_status = current_status
        self.attempted_transition = attempted_transition
        super().__init__(
            f"Cannot '{attempted_transition}' {entity_type}(id={entity_id}) "
            f"while it is in status '{current_status}'."
        )
