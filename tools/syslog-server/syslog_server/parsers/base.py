"""
Base parser class and interfaces.

Defines the abstract interface for all log parsers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypeAlias

from pydantic import BaseModel, Field

from syslog_server.storage.models import LogEntry


# Type alias for parse result
ParseResult: TypeAlias = LogEntry | None


class ParserConfig(BaseModel):
    """Base configuration for parsers."""

    enabled: bool = Field(default=True, description="Whether the parser is enabled")
    priority: int = Field(default=100, description="Parser priority (lower is higher)")
    strict_mode: bool = Field(default=False, description="Enable strict parsing mode")
    default_tags: list[str] = Field(default_factory=list, description="Default tags to add")
    default_severity: int = Field(default=6, description="Default severity (0-7)")


class BaseParser(ABC):
    """
    Abstract base class for log parsers.

    All parsers must inherit from this class and implement the parse method.
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        """
        Initialize the parser.

        Args:
            config: Parser configuration
        """
        self.config = config or ParserConfig()
        self.name = self.__class__.__name__

    @abstractmethod
    def can_parse(self, message: str) -> bool:
        """
        Check if this parser can handle the given message.

        Args:
            message: Raw log message

        Returns:
            True if this parser can parse the message
        """
        pass

    @abstractmethod
    def parse(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """
        Parse a log message into a LogEntry.

        Args:
            message: Raw log message
            source_ip: IP address of the source device
            received_at: When the message was received (defaults to now)

        Returns:
            LogEntry if parsing succeeded, None otherwise
        """
        pass

    def parse_safe(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """
        Parse a log message with error handling.

        Args:
            message: Raw log message
            source_ip: IP address of the source device
            received_at: When the message was received (defaults to now)

        Returns:
            LogEntry if parsing succeeded, None otherwise
        """
        try:
            if not self.can_parse(message):
                return None
            return self.parse(message, source_ip, received_at)
        except Exception:
            # Log parsing errors are handled by the manager
            return None

    def create_base_entry(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
        timestamp: datetime | None = None,
    ) -> LogEntry:
        """
        Create a base LogEntry with common fields.

        Args:
            message: Raw log message
            source_ip: IP address of the source device
            received_at: When the message was received
            timestamp: Original timestamp from the log

        Returns:
            LogEntry with base fields populated
        """
        now = received_at or datetime.now()
        ts = timestamp or now

        return LogEntry(
            received_at=now,
            timestamp=ts,
            device_ip=source_ip,
            device_type="unknown",
            severity=self.config.default_severity,
            message=message,
            raw_message=message,
            tags=self.config.default_tags.copy() if self.config.default_tags else None,
        )

    @staticmethod
    def severity_from_priority(priority: int) -> tuple[int, str]:
        """
        Extract severity from syslog priority value.

        Args:
            priority: Syslog priority value (0-191)

        Returns:
            Tuple of (severity_level, severity_label)
        """
        severity = priority & 0x07  # Lower 3 bits
        labels = {
            0: "emerg",
            1: "alert",
            2: "crit",
            3: "err",
            4: "warning",
            5: "notice",
            6: "info",
            7: "debug",
        }
        return severity, labels.get(severity, "unknown")

    @staticmethod
    def facility_from_priority(priority: int) -> tuple[int, str]:
        """
        Extract facility from syslog priority value.

        Args:
            priority: Syslog priority value (0-191)

        Returns:
            Tuple of (facility_code, facility_name)
        """
        facility = priority >> 3  # Upper bits
        facilities = {
            0: "kern",
            1: "user",
            2: "mail",
            3: "daemon",
            4: "auth",
            5: "syslog",
            6: "lpr",
            7: "news",
            8: "uucp",
            9: "cron",
            10: "authpriv",
            11: "ftp",
            12: "ntp",
            13: "security",
            14: "console",
            15: "cron2",
            16: "local0",
            17: "local1",
            18: "local2",
            19: "local3",
            20: "local4",
            21: "local5",
            22: "local6",
            23: "local7",
        }
        return facility, facilities.get(facility, f"facility-{facility}")

    def normalize_hostname(self, hostname: str | None) -> str | None:
        """
        Normalize hostname field.

        Args:
            hostname: Raw hostname value

        Returns:
            Normalized hostname or None
        """
        if not hostname:
            return None
        hostname = hostname.strip()
        if hostname in ["-", "", "none"]:
            return None
        return hostname

    def normalize_message(self, message: str) -> str:
        """
        Normalize message content.

        Args:
            message: Raw message

        Returns:
            Normalized message
        """
        if not message:
            return ""
        # Remove extra whitespace
        message = " ".join(message.split())
        return message
