"""
Logs API routes.

Provides log query and search endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from syslog_server.storage import get_storage_manager
from syslog_server.storage.models import LogEntry, LogQuery, PaginatedResult

router = APIRouter()


class ApiResponse(BaseModel):
    """Standard API response wrapper."""

    code: int = Field(description="Response code")
    message: str = Field(description="Response message")
    data: dict | None = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


@router.get("/logs", response_model=ApiResponse)
async def query_logs(
    # Time range (required)
    start_time: datetime = Query(..., description="Start time (ISO8601)"),
    end_time: datetime = Query(..., description="End time (ISO8601)"),
    # Device filters
    device_ip: str | None = Query(None, description="Device IP address"),
    device_type: str | None = Query(None, description="Device type"),
    vendor: str | None = Query(None, description="Device vendor"),
    # Event filters
    event_type: str | None = Query(None, description="Event type"),
    severity: str | None = Query(None, description="Severity level (comma-separated)"),
    # Network filters
    src_ip: str | None = Query(None, description="Source IP address"),
    dst_ip: str | None = Query(None, description="Destination IP address"),
    port: int | None = Query(None, description="Port number"),
    protocol: str | None = Query(None, description="Protocol"),
    # Text search
    keyword: str | None = Query(None, description="Keyword search"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    # Sorting
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
):
    """Query logs with filters.

    Returns paginated results matching the query parameters.
    """
    storage_manager = get_storage_manager()
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage not available")

    # Build query
    query = LogQuery(
        start_time=start_time,
        end_time=end_time,
        device_ip=device_ip,
        device_type=device_type,
        vendor=vendor,
        event_type=event_type,
        severity=severity,
        src_ip=src_ip,
        dst_ip=dst_ip,
        port=port,
        protocol=protocol,
        keyword=keyword,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Execute query
    try:
        result = await storage_manager.query_logs(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    # Convert to response format
    return ApiResponse(
        code=200,
        message="success",
        data={
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "logs": [log.model_dump(mode="json") for log in result.logs],
        },
    )


@router.get("/logs/{log_id}", response_model=ApiResponse)
async def get_log(log_id: int):
    """Get a specific log entry by ID.

    Args:
        log_id: Log entry ID

    Returns:
        Log entry details
    """
    storage_manager = get_storage_manager()
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage not available")

    # TODO: Implement single log retrieval
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/logs/search", response_model=ApiResponse)
async def search_logs(request: dict):
    """Advanced log search with complex filters.

    Allows complex queries with boolean operators and aggregations.

    Args:
        request: Search query specification

    Returns:
        Search results
    """
    # TODO: Implement advanced search
    raise HTTPException(status_code=501, detail="Not implemented")


# Storage manager dependency (simplified for now)
_storage_manager = None


def get_storage_manager():
    """Get the storage manager instance."""
    return _storage_manager


def set_storage_manager(manager):
    """Set the storage manager instance."""
    global _storage_manager
    _storage_manager = manager
