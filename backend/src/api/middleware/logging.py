import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.utils.metrics import metrics_store

logger = structlog.get_logger(__name__)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or retrieve correlation ID & request ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Clear existing variables and bind correlation details
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        
        try:
            response: Response = await call_next(request)
            process_time = time.perf_counter() - start_time
            
            # Record metrics
            metrics_store.record_request(
                path=request.url.path,
                latency=process_time,
                status_code=response.status_code
            )

            # Log request completion details
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_seconds=round(process_time, 4),
                client_host=request.client.host if request.client else "unknown",
            )
            
            # Inject headers back into response
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            process_time = time.perf_counter() - start_time
            metrics_store.record_request(
                path=request.url.path,
                latency=process_time,
                status_code=500
            )
            
            logger.error(
                "Request failed",
                exc_info=exc,
                duration_seconds=round(process_time, 4),
            )
            raise exc
