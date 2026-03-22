"""
SQLAlchemy ORM models for Syslog Server.

Defines database table schemas.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, SmallInteger, Text, JSON, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class LogsTable(Base):
    """ORM model for the logs table."""

    __tablename__ = "logs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    message_ts: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Device information
    device_ip: Mapped[str] = mapped_column(String(45))  # Support IPv6
    device_type: Mapped[str] = mapped_column(String(50), index=True)
    device_hostname: Mapped[str | None] = mapped_column(String(100))
    vendor: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))

    # Event information
    event_type: Mapped[str | None] = mapped_column(String(50))
    event_category: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[int] = mapped_column(SmallInteger)
    severity_label: Mapped[str | None] = mapped_column(String(20))
    event_code: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)

    # Network information
    src_ip: Mapped[str | None] = mapped_column(String(45))
    src_port: Mapped[int | None] = mapped_column(Integer)
    dst_ip: Mapped[str | None] = mapped_column(String(45))
    dst_port: Mapped[int | None] = mapped_column(Integer)
    protocol: Mapped[str | None] = mapped_column(String(10))
    src_geo_country: Mapped[str | None] = mapped_column(String(50))
    src_geo_city: Mapped[str | None] = mapped_column(String(50))

    # Threat information
    action: Mapped[str | None] = mapped_column(String(20))
    threat_id: Mapped[str | None] = mapped_column(String(100))
    attack_pattern: Mapped[str | None] = mapped_column(String(100))
    risk_score: Mapped[int | None] = mapped_column(SmallInteger)

    # Raw and parsed data
    raw_message: Mapped[str] = mapped_column(Text)
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Tags (stored as JSON array for PostgreSQL 9.2 compatibility)
    tags: Mapped[list[str] | None] = mapped_column(JSON)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        """String representation."""
        return f"<LogsTable(id={self.id}, device_ip={self.device_ip}, ts={self.message_ts})>"
