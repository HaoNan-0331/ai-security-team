"""
FastAPI application factory for Syslog Server.

Creates and configures the FastAPI application with all routes.
"""

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from syslog_server.config import settings
from syslog_server.api.routes.health import router as health_router
from syslog_server.api.routes.logs import router as logs_router
from syslog_server.utils.metrics import metrics


logger = structlog.get_logger(__name__)


def create_api_app(lifespan: Callable | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        lifespan: Optional lifespan context manager

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Syslog Server API",
        description="Enterprise log collection and analysis system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_hosts,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register middleware
    app.middleware("http")(log_requests)
    app.middleware("http")(add_request_id)

    # Register routers
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(logs_router, prefix="/api/v1", tags=["Logs"])

    # Exception handlers
    app.add_exception_handler(Exception, global_exception_handler)

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("API server starting", version="1.0.0")

    return app


async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Update metrics
    metrics.api_requests.labels(
        endpoint=request.url.path,
        method=request.method,
        status=response.status_code,
    ).inc()
    metrics.api_duration.labels(endpoint=request.url.path).observe(duration)

    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{duration:.3f}s",
    )

    return response


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "detail": str(exc) if settings.log_level == "DEBUG" else None,
        },
    )
