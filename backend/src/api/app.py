"""
ASEP — FastAPI Application Factory
====================================
Creates and configures the FastAPI application instance.

Design decisions:
  - Application factory pattern keeps the app testable (no global state).
  - Lifespan context manager handles startup / shutdown hooks cleanly.
  - All routers are registered here; business logic lives in services.

TODO (Phase 0.2):
    - Add OpenTelemetry instrumentation middleware
    - Add rate-limiting middleware
    - Add request-id middleware
    - Register agent supervisor lifespan
    - Add Prometheus /metrics endpoint
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exceptions import register_exception_handlers
from src.api.routers import health, metrics, diagnostics, ai_runtime, rag, hitl, workflows, evaluation, knowledge_sync
from src.api.routers import (
    agent_runs_router,
    tasks_router,
    memory_router,
    audit_router,
    auth_router,
    knowledge_router,
    payments_router,
)
from src.api.routers.organizations import router as organizations_router
from src.api.routers.api_keys import router as api_keys_router
from src.api.routers.projects import router as projects_router
from src.api.middleware.logging import StructuredLoggingMiddleware
from src.cache.redis import close_redis, init_redis
from src.config.settings import get_settings
from src.db.postgres import close_db, init_db
from src.utils.logging import configure_logging
import os

logger = logging.getLogger(__name__)

# Initialize Sentry backend error tracking if DSN configured
sentry_dsn = os.getenv("SENTRY_DSN_BACKEND")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            send_default_pii=True,
            integrations=[FastApiIntegration()],
        )
        logger.info("Sentry backend error tracking initialized.")
    except Exception as exc:
        logger.warning("Failed to initialize Sentry SDK: %s", exc)




@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown of all critical services:
      - Structured logging configuration
      - Database connection pool initialization
      - Graceful shutdown of all services

    Startup:
        1. Configure structured logging
        2. Initialize PostgreSQL connection pool
        3. TODO: warm up LangGraph supervisor
        4. TODO: connect to Redis
        5. TODO: connect to Neo4j
        6. TODO: connect to Qdrant
        7. TODO: warm up Ollama

    Shutdown:
        1. Close all connections gracefully
    """
    settings = get_settings()
    configure_logging(
        level=settings.APP_LOG_LEVEL,
        json_logs=(settings.APP_ENV == "production")
    )
    logger.info("ASEP backend starting", extra={"version": settings.APP_VERSION, "env": settings.APP_ENV})

    # Initialize database connection pool
    await init_db()

    # Initialize redis pool
    await init_redis()

    from src.graph.neo4j import close_neo4j, init_neo4j

    # Initialize Neo4j driver — graceful degradation if unavailable at startup
    try:
        await init_neo4j()
        logger.info("Neo4j driver ready.")
    except Exception as neo4j_exc:
        logger.warning(
            "Neo4j is unavailable at startup (%s). "
            "The application will start in degraded mode — Graph endpoints will fail "
            "until Neo4j becomes reachable.",
            str(neo4j_exc),
        )


    from src.vector.qdrant import close_qdrant, init_qdrant
    from src.vector.collections import create_collection_if_not_exists

    # Initialize Qdrant client — graceful degradation if unavailable at startup.
    # RAG endpoints will fail with a clear error rather than crashing the whole app.
    try:
        await init_qdrant()
        from src.vector.qdrant import get_qdrant_client
        from src.config.settings import get_settings as _get_settings
        _settings = _get_settings()
        await create_collection_if_not_exists(
            get_qdrant_client(),
            collection_name=_settings.QDRANT_COLLECTION,
            vector_size=_settings.QDRANT_VECTOR_SIZE,
        )
        logger.info(
            "Qdrant ready — collection '%s' available.",
            _settings.QDRANT_COLLECTION,
        )
    except Exception as qdrant_exc:
        logger.warning(
            "Qdrant is unavailable at startup (%s). "
            "The application will start in degraded mode — RAG endpoints will fail "
            "until Qdrant becomes reachable.",
            str(qdrant_exc),
        )


    # TODO (Phase 0.2): await supervisor.start()

    yield

    logger.info("ASEP backend shutting down")
    # Close database connection pool gracefully
    await close_db()
    
    # Close redis pool
    await close_redis()
    
    # Close neo4j driver
    await close_neo4j()

    
    # Close qdrant client
    await close_qdrant()


def create_app() -> FastAPI:
    """
    Application factory — returns a fully configured FastAPI instance.

    Returns:
        FastAPI: The configured application.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Autonomous Software Engineering Platform — API",
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # Middleware
    # -----------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(StructuredLoggingMiddleware)

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://challenges.cloudflare.com "
            "https://checkout.razorpay.com; "
            "frame-src 'self' "
            "https://challenges.cloudflare.com "
            "https://api.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss: http: https: "
            "https://api.razorpay.com https://lumberjack.razorpay.com;"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    # -----------------------------------------------------------------------
    # Exception handlers
    # -----------------------------------------------------------------------
    register_exception_handlers(app)

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    app.include_router(health.router, tags=["Observability"])
    # app.include_router(metrics.router, tags=["Observability"])
    # app.include_router(diagnostics.router, tags=["Observability"])

    # app.include_router(auth_router, prefix="/api/v1")
    # app.include_router(agent_runs_router, prefix="/api/v1")
    # app.include_router(tasks_router, prefix="/api/v1")
    # app.include_router(memory_router, prefix="/api/v1")
    # app.include_router(audit_router, prefix="/api/v1")
    # app.include_router(knowledge_router, prefix="/api/v1")
    # app.include_router(payments_router, prefix="/api/v1")
    # app.include_router(organizations_router, prefix="/api/v1")
    # app.include_router(api_keys_router, prefix="/api/v1")
    # app.include_router(projects_router, prefix="/api/v1")
    # app.include_router(ai_runtime.router, prefix="/api/v1")
    # app.include_router(rag.router, prefix="/api/v1")
    # app.include_router(hitl.router, prefix="/api/v1")
    # app.include_router(workflows.router, prefix="/api/v1")
    # app.include_router(evaluation.router, prefix="/api/v1")
    # app.include_router(knowledge_sync.router, prefix="/api/v1")
    # from src.api.routers.monitoring import router as monitoring_router
    # app.include_router(monitoring_router, prefix="/api/v1")
    # from src.api.routers.knowledge import router as phase3_knowledge_router
    # app.include_router(phase3_knowledge_router, prefix="/api/v1")




    logger.info("FastAPI application created", extra={"routes": len(app.routes)})
    return app
