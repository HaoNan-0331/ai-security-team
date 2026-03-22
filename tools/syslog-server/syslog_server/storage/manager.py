"""
Storage manager for Syslog Server.

Manages database connections and provides storage operations.
"""

import asyncio
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from syslog_server.config import settings
from syslog_server.storage.models import LogEntry, LogQuery, PaginatedResult

logger = structlog.get_logger(__name__)


def _convert_to_sync_url(url: str) -> str:
    """Convert async PostgreSQL URL to sync URL for SQLAlchemy."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


class StorageManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str, redis_url: str):
        """Initialize storage manager.

        Args:
            database_url: PostgreSQL connection URL (async)
            redis_url: Redis connection URL
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.engine: AsyncEngine = None
        self.session_factory: Any = None
        self._redis = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connections."""
        if self._initialized:
            return

        logger.info("Initializing storage manager")

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.log_level == "DEBUG",
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )

        # Create session factory (compatible with SQLAlchemy 1.4)
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Test connection (directly use session_factory to avoid circular check)
        async with self._AsyncSessionContextManager(self.session_factory) as session:
            await session.execute(text("SELECT 1"))

        self._initialized = True
        logger.info("Storage manager initialized successfully")

    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Storage manager closed")
        self._initialized = False

    class _AsyncSessionContextManager:
        """Async context manager for database sessions (Python 3.6 compatible)."""

        def __init__(self, session_factory):
            self.session_factory = session_factory
            self.session = None

        async def __aenter__(self):
            self.session = self.session_factory()
            return self.session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.session:
                await self.session.close()

    def session(self):
        """Get a database session context manager."""
        if not self._initialized:
            raise RuntimeError("StorageManager not initialized")
        return self._AsyncSessionContextManager(self.session_factory)

    async def store_log(self, log: LogEntry) -> int:
        """Store a log entry.

        Args:
            log: Log entry to store

        Returns:
            ID of the stored log entry, or None if failed
        """
        try:
            async with self.session() as session:
                # Import here to avoid circular import
                from syslog_server.storage.schema import LogsTable

                db_log = LogsTable(
                    message_ts=log.timestamp,
                    device_ip=log.device_ip,
                    device_type=log.device_type,
                    device_hostname=log.device_hostname,
                    vendor=log.vendor,
                    model=log.model,
                    event_type=log.event_type,
                    event_category=log.event_category,
                    severity=log.severity,
                    severity_label=log.severity_label,
                    event_code=log.event_code,
                    message=log.message,
                    src_ip=log.src_ip,
                    src_port=log.src_port,
                    dst_ip=log.dst_ip,
                    dst_port=log.dst_port,
                    protocol=log.protocol,
                    src_geo_country=log.src_geo_country,
                    src_geo_city=log.src_geo_city,
                    action=log.action,
                    threat_id=log.threat_id,
                    attack_pattern=log.attack_pattern,
                    risk_score=log.risk_score,
                    raw_message=log.raw_message,
                    parsed_data=log.parsed_data,
                    tags=log.tags,
                )

                session.add(db_log)
                await session.commit()
                await session.refresh(db_log)

                logger.debug("Log stored", log_id=db_log.id, device=log.device_ip)
                return db_log.id

        except Exception as e:
            logger.error("Failed to store log", error=str(e), device=log.device_ip)
            return None

    async def query_logs(self, query: LogQuery) -> PaginatedResult:
        """Query logs with filters.

        Args:
            query: Query parameters

        Returns:
            Paginated result
        """
        async with self.session() as session:
            from syslog_server.storage.schema import LogsTable

            # Build query
            stmt = select(LogsTable)

            # Apply time range filter
            stmt = stmt.where(
                LogsTable.message_ts >= query.start_time,
                LogsTable.message_ts <= query.end_time,
            )

            # Apply device filters
            if query.device_ip:
                stmt = stmt.where(LogsTable.device_ip == query.device_ip)
            if query.device_type:
                stmt = stmt.where(LogsTable.device_type == query.device_type)
            if query.vendor:
                stmt = stmt.where(LogsTable.vendor == query.vendor)

            # Apply event filters
            if query.event_type:
                stmt = stmt.where(LogsTable.event_type == query.event_type)
            if query.severity:
                # Map severity names to numbers
                severity_map = {
                    "emerg": 0,
                    "alert": 1,
                    "crit": 2,
                    "err": 3,
                    "warning": 4,
                    "notice": 5,
                    "info": 6,
                    "debug": 7,
                }
                severities = query.severity.split(",")
                levels = [severity_map.get(s, 7) for s in severities]
                stmt = stmt.where(LogsTable.severity.in_(levels))

            # Apply network filters
            if query.src_ip:
                stmt = stmt.where(LogsTable.src_ip == query.src_ip)
            if query.dst_ip:
                stmt = stmt.where(LogsTable.dst_ip == query.dst_ip)
            if query.port:
                stmt = stmt.where(
                    (LogsTable.src_port == query.port) | (LogsTable.dst_port == query.port)
                )
            if query.protocol:
                stmt = stmt.where(LogsTable.protocol.ilike(query.protocol))

            # Apply text search
            if query.keyword:
                stmt = stmt.where(LogsTable.message.ilike("%" + query.keyword + "%"))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one()

            # Apply sorting
            order_col = getattr(LogsTable, query.sort_by, LogsTable.message_ts)
            if query.sort_order == "desc":
                stmt = stmt.order_by(desc(order_col))
            else:
                stmt = stmt.order_by(order_col)

            # Apply pagination
            offset = (query.page - 1) * query.page_size
            stmt = stmt.limit(query.page_size).offset(offset)

            # Execute query
            result = await session.execute(stmt)
            rows = result.scalars().all()

            # Convert to LogEntry models
            logs = [self._row_to_log_entry(row) for row in rows]

            return PaginatedResult.create(logs, total, query.page, query.page_size)

    def _row_to_log_entry(self, row) -> LogEntry:
        """Convert database row to LogEntry model."""
        return LogEntry(
            id=row.id,
            received_at=row.received_at,
            timestamp=row.message_ts,
            device_ip=str(row.device_ip),
            device_type=row.device_type,
            device_hostname=row.device_hostname,
            vendor=row.vendor,
            model=row.model,
            event_type=row.event_type,
            event_category=row.event_category,
            severity=row.severity,
            severity_label=row.severity_label,
            event_code=row.event_code,
            message=row.message,
            src_ip=str(row.src_ip) if row.src_ip else None,
            src_port=row.src_port,
            dst_ip=str(row.dst_ip) if row.dst_ip else None,
            dst_port=row.dst_port,
            protocol=row.protocol,
            src_geo_country=row.src_geo_country,
            src_geo_city=row.src_geo_city,
            action=row.action,
            threat_id=row.threat_id,
            attack_pattern=row.attack_pattern,
            risk_score=row.risk_score,
            raw_message=row.raw_message,
            parsed_data=row.parsed_data,
            tags=row.tags,
        )

    async def get_stats(self) -> Any:
        """Get storage statistics."""
        async with self.session() as session:
            from syslog_server.storage.schema import LogsTable

            # Get total count
            count_stmt = select(func.count()).select_from(LogsTable)
            result = await session.execute(count_stmt)
            total = result.scalar_one()

            # Get counts by device type
            device_stmt = select(
                LogsTable.device_type,
                func.count().label("count")
            ).group_by(LogsTable.device_type)
            device_result = await session.execute(device_stmt)
            by_device = {row.device_type: row.count for row in device_result}

            # Get counts by severity
            severity_stmt = select(
                LogsTable.severity_label,
                func.count().label("count")
            ).where(LogsTable.severity_label.isnot(None)).group_by(LogsTable.severity_label)
            severity_result = await session.execute(severity_stmt)
            by_severity = {row.severity_label: row.count for row in severity_result}

            return {
                "total": total,
                "by_device_type": by_device,
                "by_severity": by_severity,
            }
