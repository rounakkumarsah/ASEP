"""
ASEP — Health & Readiness Endpoints
======================================
Every service in the platform exposes:

  GET /health  — liveness probe  (is the process alive?)
  GET /ready   — readiness probe (are all dependencies reachable?)

These endpoints are consumed by:
  - Docker Compose healthchecks
  - Kubernetes liveness / readiness probes
  - Uptime monitoring

Implementation notes:
  - /health is always 200 as long as the process runs
  - /ready checks connectivity to all critical dependencies asynchronously
  - Individual dependency status is returned for debugging
"""

from __future__ import annotations

import logging
import platform
import time
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.config.settings import get_settings
from src.db.postgres import check_db_health

logger = logging.getLogger(__name__)
router = APIRouter()

# Application start time (used to compute uptime)
_START_TIME: float = time.monotonic()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    python_version: str


class DependencyStatus(BaseModel):
    """Status of a single external dependency."""

    name: str
    status: str  # "ok" | "degraded" | "unavailable"
    latency_ms: float | None = None
    detail: str | None = None


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: str  # "ready" | "degraded" | "not_ready"
    dependencies: list[DependencyStatus]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns 200 if the service process is alive.",
)
async def health_check() -> HealthResponse:
    """
    Liveness probe — always returns 200 while the process is running.

    This endpoint is used by container orchestrators (Docker, Kubernetes)
    to determine if the service process is still alive.

    It does NOT check dependencies; use /ready for that.
    """
    settings = get_settings()
    uptime = time.monotonic() - _START_TIME
    logger.debug("Health check called", extra={"uptime_seconds": uptime})
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        uptime_seconds=round(uptime, 2),
        python_version=platform.python_version(),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Returns 200 if all critical dependencies are reachable.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe — checks connectivity to all external dependencies.

    Returns 200 only if all critical dependencies are reachable.
    Individual dependency status is returned for debugging.

    Used by:
        - Container orchestrators (Docker, Kubernetes) for load balancing
        - Monitoring systems to detect service degradation
        - Deployment pipelines to validate readiness

    Returns:
        ReadinessResponse: Overall status + individual dependency details
    """
    deps: list[DependencyStatus] = []

    # Check PostgreSQL
    db_healthy, db_detail, db_latency = await check_db_health()
    deps.append(
        DependencyStatus(
            name="postgres",
            status="ok" if db_healthy else "unavailable",
            latency_ms=db_latency,
            detail=db_detail,
        )
    )

    from src.cache.health import redis_health_check
    redis_healthy = await redis_health_check()
    deps.append(
        DependencyStatus(
            name="redis",
            status="ok" if redis_healthy else "unavailable",
            detail="Redis ping successful" if redis_healthy else "Redis ping failed",
        )
    )

    from src.graph.health import neo4j_health_check
    neo4j_healthy = await neo4j_health_check()
    deps.append(
        DependencyStatus(
            name="neo4j",
            status="ok" if neo4j_healthy else "unavailable",
            detail="Neo4j ping successful" if neo4j_healthy else "Neo4j ping failed",
        )
    )

    # TODO (Phase 0.2): ping Qdrant via qdrant_client
    # deps.append(DependencyStatus(name="qdrant", status="unknown", detail="TODO: implement ping"))

    # TODO (Phase 0.2): ping Ollama via httpx
    # deps.append(DependencyStatus(name="ollama", status="unknown", detail="TODO: implement ping"))

    # Determine overall status
    all_ok = all(dep.status == "ok" for dep in deps)
    overall_status = "ready" if all_ok else "degraded"

    if not all_ok:
        logger.warning(
            "Readiness check failed",
            extra={"status": overall_status, "dependencies": [d.name for d in deps if d.status != "ok"]},
        )

    return ReadinessResponse(status=overall_status, dependencies=deps)
