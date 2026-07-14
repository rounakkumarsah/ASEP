"""
Audit Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.common import ORMBaseModel
from src.db.models.audit_log import ActorType, AuditOutcome, AuditSeverity


class AuditLogResponse(ORMBaseModel):
    """Presentation model for an Audit Log."""
    id: uuid.UUID
    actor_type: ActorType
    actor_id: str
    action: str
    resource_type: str
    resource_id: str | None
    severity: AuditSeverity
    outcome: AuditOutcome
    request_id: uuid.UUID | None
    correlation_id: uuid.UUID | None
    trace_id: str | None
    span_id: str | None
    ip_address: str | None
    user_agent: str | None
    log_details: dict[str, Any] | None
    duration_ms: int | None
    created_at: datetime
