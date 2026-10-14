"""
ASEP — Startup Readiness Probe
===============================
Provides an endpoint to determine when ASEP has completely finished cold-start
initialization and all core dependencies (Postgres, Qdrant, Neo4j, License manager)
are reachable.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Response, status

from src.config.settings import get_settings
from src.db.postgres import check_db_health
from src.graph.health import neo4j_health_check
from src.licensing.license_manager import get_license_manager
from src.vector.health import qdrant_health_check

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Observability"])


@router.get(
    "/health/ready",
    summary="Startup Readiness Probe",
    description="Returns 200 only after Postgres, Qdrant, Neo4j, and License manager are ready.",
    response_description="Readiness status of all critical platform dependencies",
)
async def check_readiness(response: Response) -> dict[str, Any]:
    """
    Startup readiness probe.

    Returns:
        200 {"status": "ready", "checks": {...}} if all deps reachable.
        503 {"status": "not_ready", "checks": {...}} if any dep is unreachable.
    """
    # 1. Postgres
    try:
        db_healthy, _, _ = await check_db_health()
        postgres_ok = bool(db_healthy)
    except Exception as exc:
        logger.warning("Postgres readiness check failed: %s", exc)
        postgres_ok = False

    # 2. Qdrant
    try:
        qdrant_ok = bool(await qdrant_health_check())
    except Exception as exc:
        logger.warning("Qdrant readiness check failed: %s", exc)
        qdrant_ok = False

    # 3. Neo4j
    try:
        neo4j_ok = bool(await neo4j_health_check())
    except Exception as exc:
        logger.warning("Neo4j readiness check failed: %s", exc)
        neo4j_ok = False

    # 4. License manager has loaded (valid or explicitly disabled)
    try:
        import os
        env_val = os.getenv("ENABLE_LICENSE_MIDDLEWARE")
        middleware_disabled = (env_val is not None and env_val.lower() in ("false", "0", "no", "off"))
        settings = get_settings()
        if middleware_disabled or not getattr(settings, "ENABLE_LICENSE_MIDDLEWARE", True):
            license_ok = True
        else:
            lm = get_license_manager()
            license_ok = bool(lm.is_licensed())
    except Exception as exc:
        logger.warning("License readiness check failed: %s", exc)
        license_ok = False

    checks: dict[str, bool] = {
        "postgres": postgres_ok,
        "qdrant": qdrant_ok,
        "neo4j": neo4j_ok,
        "license": license_ok,
    }

    all_ready = all(checks.values())

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "checks": checks}

    return {"status": "ready", "checks": checks}
