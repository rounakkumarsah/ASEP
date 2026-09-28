"""
ASEP — Quota Enforcement Middleware
===================================
Intercepts incoming agent execution requests to verify that the requesting user has not
exceeded their allocated monthly token quota. If the quota is exceeded, the request is
blocked with HTTP 402 Payment Required and the violation is recorded in the audit log.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.auth.jwt import decode_token
from src.config.settings import get_settings
from src.db.models.audit_log import (
    ActorType,
    AuditLog,
    AuditOutcome,
    AuditSeverity,
)
from src.db.models.user import User
from src.db.models.user_quota_log import UserQuotaLog
from src.db.postgres import _get_session_factory

logger = logging.getLogger(__name__)


def get_month_boundaries(target_dt: datetime.datetime | None = None) -> tuple[datetime.datetime, datetime.datetime]:
    """Calculate the UTC start and end bounds for the specified or current month."""
    dt = target_dt or datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    start_of_month = datetime.datetime(dt.year, dt.month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    if dt.month == 12:
        end_of_month = datetime.datetime(dt.year + 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    else:
        end_of_month = datetime.datetime(dt.year, dt.month + 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    return start_of_month, end_of_month


async def get_monthly_token_usage(session: Any, user_id: uuid.UUID, target_dt: datetime.datetime | None = None) -> int:
    """Query total tokens consumed by user in the target month."""
    start_dt, end_dt = get_month_boundaries(target_dt)
    stmt = select(func.coalesce(func.sum(UserQuotaLog.tokens_used), 0)).where(
        UserQuotaLog.user_id == user_id,
        UserQuotaLog.timestamp >= start_dt,
        UserQuotaLog.timestamp < end_dt,
    )
    result = await session.execute(stmt)
    return int(result.scalar_one())


class QuotaEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces monthly token quotas on agent execution endpoints.

    Intercepts:
        POST /execute-agent
        POST /api/v1/agent-runs (and variants)
    """

    INTERCEPTED_PATHS = {
        "/execute-agent",
        "/api/v1/execute-agent",
        "/agent-runs",
        "/agent-runs/",
        "/api/v1/agent-runs",
        "/api/v1/agent-runs/",
    }

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        path = request.url.path.rstrip("/")
        # Only inspect POST requests targeting agent execution endpoints
        if request.method != "POST" or (path not in self.INTERCEPTED_PATHS and not path.endswith("/execute-agent")):
            return await call_next(request)

        # 1. Resolve user token from Authorization header or cookie
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        if not token:
            token = request.cookies.get("access_token")

        user_id_str = None
        if token:
            try:
                payload = decode_token(token, self.settings.JWT_SECRET_KEY)
                user_id_str = payload.get("sub")
            except Exception as exc:
                logger.debug("Failed to decode token in quota middleware: %s", exc)

        # Allow fallback for explicit test header or downstream auth if unauthenticated
        if not user_id_str:
            user_id_str = request.headers.get("X-User-ID")

        if not user_id_str:
            # Let route handler's auth dependency handle unauthenticated response (401)
            return await call_next(request)

        try:
            user_uuid = uuid.UUID(str(user_id_str))
        except (ValueError, TypeError):
            return await call_next(request)

        # 2. Check quota against current month usage
        try:
            session_factory = _get_session_factory()
            async with session_factory() as session:
                # Query user quota
                user_stmt = select(User).where(User.id == user_uuid)
                user_result = await session.execute(user_stmt)
                user = user_result.scalar_one_or_none()

                quota = 100_000  # Default free tier quota
                if user is not None:
                    if getattr(user, "monthly_token_quota", None) is not None:
                        quota = user.monthly_token_quota
                    elif getattr(user, "current_plan", None) == "pro":
                        quota = 5_000_000
                    elif getattr(user, "current_plan", None) == "enterprise":
                        quota = 50_000_000

                # Query monthly usage
                used_tokens = await get_monthly_token_usage(session, user_uuid)

                # Check if over quota
                if used_tokens >= quota:
                    logger.warning(
                        "User %s exceeded monthly token quota (used=%d, quota=%d)",
                        user_uuid,
                        used_tokens,
                        quota,
                    )

                    # Log denied attempt to audit_logs table
                    try:
                        audit_entry = AuditLog(
                            actor_type=ActorType.USER,
                            actor_id=str(user_uuid),
                            action="agent_execution.quota_exceeded",
                            resource_type="agent_execution",
                            resource_id=None,
                            severity=AuditSeverity.WARNING,
                            outcome=AuditOutcome.FAILURE,
                            log_details={
                                "reason": "Monthly token quota exceeded",
                                "quota": quota,
                                "tokens_used": used_tokens,
                                "path": request.url.path,
                            },
                        )
                        session.add(audit_entry)
                        await session.commit()
                    except Exception as audit_exc:
                        logger.error("Failed to write quota denial audit log: %s", audit_exc)

                    return JSONResponse(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        content={
                            "detail": "Monthly token quota exceeded. Please upgrade your plan.",
                            "quota": quota,
                            "tokens_used": used_tokens,
                        },
                    )

        except Exception as exc:
            # High-resilience: do not block request if database check experiences transient error
            logger.error("Error executing quota check in middleware: %s", exc)

        return await call_next(request)
