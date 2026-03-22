"""
Data models for Syslog Server.

Defines Pydantic models for log entries and queries.
"""

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LogEntry(BaseModel):
    """A single log entry."""

    # Identification
    id: int | None = Field(default=None, description="Log entry ID")
    received_at: datetime = Field(description="When the log was received")

    # Timestamp
    timestamp: datetime = Field(description="Original timestamp from the log message")

    # Device information
    device_ip: str = Field(description="Device IP address")
    device_type: str = Field(description="Device type (firewall/switch/router/etc)")
    device_hostname: str | None = Field(default=None, description="Device hostname")
    vendor: str | None = Field(default=None, description="Device vendor")
    model: str | None = Field(default=None, description="Device model")

    # Event information
    event_type: str | None = Field(default=None, description="Event type")
    event_category: str | None = Field(default=None, description="Event category")
    severity: int = Field(description="Severity level (0-7)")
    severity_label: str | None = Field(default=None, description="Severity label")
    event_code: str | None = Field(default=None, description="Event code")
    message: str = Field(description="Log message")

    # Network information
    src_ip: str | None = Field(default=None, description="Source IP address")
    src_port: int | None = Field(default=None, description="Source port")
    dst_ip: str | None = Field(default=None, description="Destination IP address")
    dst_port: int | None = Field(default=None, description="Destination port")
    protocol: str | None = Field(default=None, description="Protocol (TCP/UDP/etc)")
    src_geo_country: str | None = Field(default=None, description="Source country")
    src_geo_city: str | None = Field(default=None, description="Source city")

    # Threat information
    action: str | None = Field(default=None, description="Action taken (accept/deny/etc)")
    threat_id: str | None = Field(default=None, description="Threat ID")
    attack_pattern: str | None = Field(default=None, description="Attack pattern/ATT&CK")
    risk_score: int | None = Field(default=None, description="Risk score (0-100)")

    # Raw data
    raw_message: str = Field(description="Original raw message")
    parsed_data: dict[str, Any] | None = Field(default=None, description="Additional parsed data")

    # Tags
    tags: list[str] | None = Field(default=None, description="Tags")

    class Config:
        """Pydantic config."""
        from_attributes = True


class LogQuery(BaseModel):
    """Query parameters for log search."""

    # Time range (required)
    start_time: datetime = Field(description="Start of time range")
    end_time: datetime = Field(description="End of time range")

    # Device filters
    device_ip: str | None = Field(default=None, description="Filter by device IP")
    device_type: str | None = Field(default=None, description="Filter by device type")
    vendor: str | None = Field(default=None, description="Filter by vendor")

    # Event filters
    event_type: str | None = Field(default=None, description="Filter by event type")
    severity: str | None = Field(default=None, description="Filter by severity (comma-separated)")

    # Network filters
    src_ip: str | None = Field(default=None, description="Filter by source IP")
    dst_ip: str | None = Field(default=None, description="Filter by destination IP")
    port: int | None = Field(default=None, description="Filter by port")
    protocol: str | None = Field(default=None, description="Filter by protocol")

    # Text search
    keyword: str | None = Field(default=None, description="Keyword search")
    regex: str | None = Field(default=None, description="Regular expression search")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Page size")

    # Sorting
    sort_by: str = Field(default="timestamp", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")

    @field_validator("severity")
    @classmethod
    def parse_severity(cls, v: str | None) -> str | None:
        """Parse severity filter."""
        if v is None:
            return None
        # Validate and normalize severity values
        valid_severities = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"]
        severities = [s.strip().lower() for s in v.split(",")]
        for sev in severities:
            if sev not in valid_severities:
                raise ValueError(f"Invalid severity: {sev}")
        return ",".join(severities)


class PaginatedResult(BaseModel):
    """Paginated query result."""

    total: int = Field(description="Total number of matching logs")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Page size")
    total_pages: int = Field(description="Total number of pages")
    logs: list[LogEntry] = Field(description="Log entries for current page")

    @classmethod
    def create(cls, logs: list[LogEntry], total: int, page: int, page_size: int) -> "PaginatedResult":
        """Create a paginated result."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            logs=logs,
        )


class HealthStatus(BaseModel):
    """Health check status."""

    status: str = Field(description="Health status (healthy/degraded/unhealthy)")
    version: str = Field(description="Server version")
    uptime: float = Field(description="Uptime in seconds")
    storage: dict = Field(description="Storage status")
    receivers: list[dict] = Field(description="Receiver status")
