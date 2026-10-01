"""
ASEP Backend — Application Entry Point
======================================
Initialises the FastAPI application and starts the Uvicorn ASGI server.

TODO (Phase 0.2):
    - Wire LangGraph supervisor on startup
    - Register agent registry
    - Add OpenTelemetry tracing
    - Add Prometheus metrics endpoint
"""

from __future__ import annotations

import uvicorn

from src.api.app import create_app
from src.config.settings import get_settings

# ---------------------------------------------------------------------------
# Application instance (imported by uvicorn / gunicorn)
# ---------------------------------------------------------------------------
app = create_app()


# ---------------------------------------------------------------------------
# Developer convenience: run directly with `python -m src.main`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )
