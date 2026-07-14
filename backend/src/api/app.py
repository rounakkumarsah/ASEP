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
from src.api.routers import health
from src.api.routers import (
    agent_runs_router,
    tasks_router,
    memory_router,
    audit_router,
    auth_router,
    knowledge_router,
)
from src.cache.redis import close_redis, init_redis
from src.config.settings import get_settings
from src.db.postgres import close_db, init_db
from src.utils.logging import configure_logging

logger = logging.getLogger(__name__)


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
    configure_logging(level=settings.APP_LOG_LEVEL)
    logger.info("ASEP backend starting", extra={"version": settings.APP_VERSION, "env": settings.APP_ENV})

    # Initialize database connection pool
    await init_db()

    # Initialize redis pool
    await init_redis()

    from src.graph.neo4j import close_neo4j, init_neo4j

    # Initialize neo4j driver
    await init_neo4j()

    # TODO (Phase 0.2): await qdrant_client.init()
    # TODO (Phase 0.2): await supervisor.start()

    yield

    logger.info("ASEP backend shutting down")
    # Close database connection pool gracefully
    await close_db()
    
    # Close redis pool
    await close_redis()
    
    # Close neo4j driver
    await close_neo4j()
    # TODO (Phase 0.2): await qdrant_client.close()


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

    # TODO (Phase 0.2): add request-id middleware
    # TODO (Phase 0.2): add structured-logging middleware
    # TODO (Phase 0.2): add rate-limit middleware

    # -----------------------------------------------------------------------
    # Exception handlers
    # -----------------------------------------------------------------------
    register_exception_handlers(app)

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    app.include_router(health.router, tags=["Observability"])

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(agent_runs_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")

    logger.info("FastAPI application created", extra={"routes": len(app.routes)})
    return app
