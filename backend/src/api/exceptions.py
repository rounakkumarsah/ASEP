"""
ASEP — API Exception Handlers
=============================
Maps domain and ORM exceptions to FastAPI HTTP responses.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from src.api.schemas.common import ErrorResponse
from src.services.exceptions import InvalidStateError

logger = logging.getLogger(__name__)


async def no_result_found_handler(request: Request, exc: NoResultFound) -> JSONResponse:
    """Map SQLAlchemy NoResultFound to HTTP 404 Not Found."""
    error = ErrorResponse(
        error_code="NOT_FOUND",
        message="The requested resource was not found.",
        details={"path": request.url.path}
    )
    return JSONResponse(status_code=404, content=error.model_dump())


async def invalid_state_error_handler(request: Request, exc: InvalidStateError) -> JSONResponse:
    """Map domain InvalidStateError to HTTP 409 Conflict."""
    error = ErrorResponse(
        error_code="INVALID_STATE",
        message=str(exc),
        details={
            "entity_type": exc.entity_type,
            "entity_id": str(exc.entity_id),
            "current_status": exc.current_status,
            "attempted_transition": exc.attempted_transition,
        }
    )
    return JSONResponse(status_code=409, content=error.model_dump())


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Map ValueError (often from service validation) to HTTP 400 Bad Request."""
    error = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message=str(exc),
    )
    return JSONResponse(status_code=400, content=error.model_dump())


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected 500 errors."""
    logger.exception("Unexpected unhandled exception")
    error = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )
    return JSONResponse(status_code=500, content=error.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers with the FastAPI app."""
    app.add_exception_handler(NoResultFound, no_result_found_handler)
    app.add_exception_handler(InvalidStateError, invalid_state_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    # The global catch-all is optional but ensures standardized ErrorResponse bodies.
    app.add_exception_handler(Exception, unexpected_error_handler)
