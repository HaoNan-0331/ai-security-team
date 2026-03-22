"""
Health check API routes.

Provides health status and system information.
"""

import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from syslog_server.storage.models import HealthStatus
from syslog_server.storage import get_storage_manager

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def get_health():
    """Get system health status.

    Returns:
        Health status including version, uptime, and component status
    """
    # TODO: Get real uptime
    uptime = 0  # Replace with actual uptime tracking

    # TODO: Check storage manager status
    storage_manager = get_storage_manager()
    storage_status = {
        "status": "connected" if storage_manager and storage_manager._initialized else "disconnected",
    }

    # TODO: Get receiver status from receiver manager
    receivers = [
        {"name": "514/udp", "status": "listening", "rate": 0},
        {"name": "514/tcp", "status": "listening", "rate": 0},
        {"name": "515/tcp", "status": "listening", "rate": 0},
        {"name": "516/tcp", "status": "listening", "rate": 0},
    ]

    overall_status = "healthy"
    if storage_status.get("status") != "connected":
        overall_status = "degraded"
    if not any(r["status"] == "listening" for r in receivers):
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        version="1.0.0",
        uptime=uptime,
        storage=storage_status,
        receivers=receivers,
    )


@router.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics.

    Returns:
        Prometheus text format metrics
    """
    from syslog_server.utils.metrics import metrics

    metrics_data = metrics.export()
    return Response(content=metrics_data, media_type="text/plain")
