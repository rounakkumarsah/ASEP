"""
ASEP — License Enforcement Middleware
======================================
Intercepts incoming HTTP requests and ensures the application holds a valid,
offline-verified license key before serving protected endpoints.
Exempts public endpoints (health, auth, OpenAPI docs, and static assets).
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from src.config.settings import get_settings
from src.licensing.license_manager import get_license_manager

logger = structlog.get_logger(__name__)

import posixpath
from urllib.parse import unquote

# Explicitly exempt paths and pattern matchers
WHITELIST_EXACT = {
    "/",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/health",
    "/api/v1/health/ready",
    "/health",
    "/health/ready",
    "/ready",
    "/metrics",
}

WHITELIST_PREFIXES = (
    "/api/v1/auth",
    "/auth",
    "/api/auth",
    "/api/v1/health",
    "/api/health",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
)

STATIC_EXTENSIONS = (
    ".html",
    ".css",
    ".js",
    ".ico",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
)


def normalize_path(path: str) -> str:
    """Normalize URL-encoded characters and resolve dot/traversal segments."""
    decoded = unquote(path)
    normalized = posixpath.normpath(decoded)
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized


def is_path_exempt(path: str) -> bool:
    """Return True if request path does not require a license."""
    norm_path = normalize_path(path)

    if norm_path in WHITELIST_EXACT:
        return True

    for prefix in WHITELIST_PREFIXES:
        if norm_path == prefix or norm_path.startswith(prefix + "/"):
            return True

    # Static file extensions apply only to non-API routes (e.g. root static files or assets)
    if not norm_path.startswith("/api/"):
        if norm_path.endswith(STATIC_EXTENSIONS):
            return True

    return False


class LicenseGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces valid ASEP license for all non-whitelisted routes.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Pass CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check toggle: skip license checks if disabled
        settings = get_settings()
        if not getattr(settings, "ENABLE_LICENSE_MIDDLEWARE", True):
            return await call_next(request)

        env_val = os.getenv("ENABLE_LICENSE_MIDDLEWARE")
        if env_val is not None and env_val.lower() in ("false", "0", "no", "off"):
            return await call_next(request)

        path = request.url.path

        # Whitelist and license-exempt prefixes pass through
        if is_path_exempt(path):
            return await call_next(request)

        # Check license validity
        lm = get_license_manager()
        if not lm.is_licensed():
            # If env key is present, retry verification if not already attempted for this key
            current_key = os.getenv("ASEP_LICENSE_KEY")
            if current_key and getattr(lm, "_last_attempted_key", None) != current_key:
                lm._load_and_verify()
                lm._last_attempted_key = current_key

        if not lm.is_licensed():
            logger.warning(
                "license_middleware_blocked",
                path=path,
                method=request.method,
            )
            return JSONResponse(
                status_code=402,
                content={"detail": "License required. Set ASEP_LICENSE_KEY in .env."},
            )

        return await call_next(request)
