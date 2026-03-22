"""
Syslog parser for RFC3164 and RFC5424 formats.

Supports parsing of both traditional BSD syslog (RFC3164) and the newer
syslog format (RFC5424) with structured data.
"""

import re
from datetime import datetime
from typing import Any

import structlog

from syslog_server.parsers.base import BaseParser, ParseResult, ParserConfig
from syslog_server.utils.metrics import metrics


logger = structlog.get_logger(__name__)


class SyslogParser(BaseParser):
    """
    Parser for Syslog messages in RFC3164 and RFC5424 formats.

    RFC3164 format: <PRI>MON DD HH:MM:SS HOSTNAME TAG: MSG
    RFC5424 format: <PRI>VERSION ISOTIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    """

    # RFC3164 pattern: <34>Oct 11 22:14:15 mymachine su: 'su root' failed for user on /dev/pts/8
    RFC3164_PATTERN = re.compile(
        r"""^
        <(?P<pri>\d{1,3})>                     # Priority value
        (?P<timestamp>[A-Za-z]{3}\s+\d{1,2}\s+  # Month Day
        \d{2}:\d{2}:\d{2})\s+                   # HH:MM:SS
        (?P<hostname>[^\s]+)\s+                  # Hostname
        (?P<tag>[^\s:]+?):?\s*                   # Tag (process name) with optional colon
        (?P<message>.*)$                         # Message content
        """,
        re.VERBOSE,
    )

    # RFC5424 pattern: <34>1 2003-10-11T22:14:15.003Z mymachine.example.com su - ID47 [exampleSDID@32473 iut="3" eventSource="Application"]
    RFC5424_PATTERN = re.compile(
        r"""^
        <(?P<pri>\d{1,3})>                      # Priority value
        (?P<version>\d+)\s+                      # Version (must be 1)
        (?P<timestamp>
            \d{4}-\d{2}-\d{2}T                  # ISO date
            \d{2}:\d{2}:\d{2}                   # Time
            (?:\.\d+)?                           # Fractional seconds (optional)
            (?:Z|[+-]\d{2}:\d{2})?              # Timezone (optional)
        )\s+
        (?P<hostname>[^\s]+)\s+                  # Hostname or IP
        (?P<app_name>[^\s]+)\s+                  # Application name
        (?P<proc_id>[^\s]+)\s+                   # Process ID
        (?P<msg_id>[^\s]+)\s+                    # Message ID
        (?P<structured_data>(?:\[.*?\])*|-)\s*   # Structured data (empty= -)
        (?P<message>.*)$                         # Message content
        """,
        re.VERBOSE,
    )

    # Simple priority pattern for fallback
    PRIORITY_PATTERN = re.compile(r"^<(\d{1,3})>")

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize the Syslog parser."""
        super().__init__(config)
        self._parse_rfc3164_count = 0
        self._parse_rfc5424_count = 0

    def can_parse(self, message: str) -> bool:
        """Check if message looks like a syslog message."""
        if not message:
            return False
        return bool(self.PRIORITY_PATTERN.match(message))

    def parse(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Parse a syslog message."""
        # Try RFC5424 first (newer format)
        rfc5424_match = self.RFC5424_PATTERN.match(message)
        if rfc5424_match:
            return self._parse_rfc5424(rfc5424_match, message, source_ip, received_at)

        # Try RFC3164 (older format)
        rfc3164_match = self.RFC3164_PATTERN.match(message)
        if rfc3164_match:
            return self._parse_rfc3164(rfc3164_match, message, source_ip, received_at)

        # Fallback: try to extract at least priority
        return self._parse_fallback(message, source_ip, received_at)

    def _parse_rfc3164(
        self,
        match: re.Match,
        raw_message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Parse RFC3164 (BSD) syslog format."""
        try:
            groups = match.groupdict()
            priority = int(groups["pri"])
            severity, severity_label = self.severity_from_priority(priority)
            facility, facility_name = self.facility_from_priority(priority)

            # Parse timestamp (add current year since RFC3164 doesn't include it)
            timestamp_str = groups["timestamp"]
            try:
                # RFC3164 timestamp format: Oct 11 22:14:15
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            except ValueError:
                timestamp = received_at or datetime.now()

            # Extract hostname
            hostname = self.normalize_hostname(groups["hostname"])

            # Create base entry
            entry = self.create_base_entry(
                message=groups["message"],
                source_ip=source_ip,
                received_at=received_at,
                timestamp=timestamp,
            )

            # Update with parsed fields
            entry.device_hostname = hostname
            entry.severity = severity
            entry.severity_label = severity_label
            entry.message = self.normalize_message(groups["message"])

            # Extract process name from tag
            tag = groups.get("tag", "")
            if tag:
                # Remove PID if present (e.g., "sshd[12345]")
                process_name = re.sub(r"\[\d+\]$", "", tag)
                entry.device_type = process_name

            # Store additional parsed data
            parsed_data = {
                "format": "rfc3164",
                "priority": priority,
                "facility": facility,
                "facility_name": facility_name,
                "tag": tag,
            }
            entry.parsed_data = parsed_data

            self._parse_rfc3164_count += 1
            metrics.messages_parsed.labels(parser=self.name, status="success").inc()

            return entry

        except Exception as e:
            logger.warning("Failed to parse RFC3164 message", error=str(e), message=raw_message[:100])
            metrics.messages_parsed.labels(parser=self.name, status="error").inc()
            metrics.parse_errors.labels(parser=self.name, error_type="rfc3164_parse").inc()
            return None

    def _parse_rfc5424(
        self,
        match: re.Match,
        raw_message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Parse RFC5424 syslog format."""
        try:
            groups = match.groupdict()
            priority = int(groups["pri"])
            severity, severity_label = self.severity_from_priority(priority)
            facility, facility_name = self.facility_from_priority(priority)

            # Parse ISO timestamp
            timestamp_str = groups["timestamp"]
            try:
                # Handle various timezone formats
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = received_at or datetime.now()

            # Extract hostname
            hostname = self.normalize_hostname(groups["hostname"])

            # Create base entry
            message = groups["message"] or ""
            entry = self.create_base_entry(
                message=message,
                source_ip=source_ip,
                received_at=received_at,
                timestamp=timestamp,
            )

            # Update with parsed fields
            entry.device_hostname = hostname
            entry.severity = severity
            entry.severity_label = severity_label
            entry.message = self.normalize_message(message)

            # App name as device type
            app_name = groups.get("app_name", "-")
            if app_name and app_name != "-":
                entry.device_type = app_name

            # Parse structured data
            structured_data = groups.get("structured_data", "")
            parsed_data = {
                "format": "rfc5424",
                "priority": priority,
                "facility": facility,
                "facility_name": facility_name,
                "version": int(groups.get("version", "1")),
                "app_name": app_name,
                "proc_id": groups.get("proc_id"),
                "msg_id": groups.get("msg_id"),
            }

            if structured_data and structured_data != "-":
                sd_elements = self._parse_structured_data(structured_data)
                parsed_data["structured_data"] = sd_elements

                # Extract common fields from structured data
                self._extract_structured_data_fields(entry, sd_elements)

            entry.parsed_data = parsed_data

            self._parse_rfc5424_count += 1
            metrics.messages_parsed.labels(parser=self.name, status="success").inc()

            return entry

        except Exception as e:
            logger.warning("Failed to parse RFC5424 message", error=str(e), message=raw_message[:100])
            metrics.messages_parsed.labels(parser=self.name, status="error").inc()
            metrics.parse_errors.labels(parser=self.name, error_type="rfc5424_parse").inc()
            return None

    def _parse_fallback(
        self,
        raw_message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Fallback parser for messages with only priority."""
        try:
            priority_match = self.PRIORITY_PATTERN.match(raw_message)
            if not priority_match:
                return None

            priority = int(priority_match.group(1))
            severity, severity_label = self.severity_from_priority(priority)
            facility, facility_name = self.facility_from_priority(priority)

            # Remove priority from message
            message = raw_message[priority_match.end():]

            entry = self.create_base_entry(
                message=message,
                source_ip=source_ip,
                received_at=received_at,
            )

            entry.severity = severity
            entry.severity_label = severity_label
            entry.message = self.normalize_message(message)

            entry.parsed_data = {
                "format": "syslog_fallback",
                "priority": priority,
                "facility": facility,
                "facility_name": facility_name,
            }

            metrics.messages_parsed.labels(parser=self.name, status="partial").inc()
            return entry

        except Exception as e:
            logger.warning("Failed to parse message (fallback)", error=str(e), message=raw_message[:100])
            metrics.parse_errors.labels(parser=self.name, error_type="fallback_parse").inc()
            return None

    def _parse_structured_data(self, sd: str) -> dict[str, Any]:
        """
        Parse RFC5424 structured data section.

        Format: [id1 param1="value1" param2="value2"][id2 param3="value3"]
        """
        result = {}

        # Pattern to match SD elements: [id param="value" ...]
        sd_pattern = re.compile(r'\[([^\s=]+)\s+(.*?)\](?=\s*\[|$)')

        for match in sd_pattern.finditer(sd):
            sd_id = match.group(1)
            params_str = match.group(2)

            # Parse key-value pairs
            params = {}
            kv_pattern = re.compile(r'(\w+)="(.*?)"')
            for kv_match in kv_pattern.finditer(params_str):
                key = kv_match.group(1)
                value = kv_match.group(2)
                params[key] = value

            result[sd_id] = params

        return result

    def _extract_structured_data_fields(self, entry: "LogEntry", sd_data: dict) -> None:
        """Extract common fields from structured data."""
        for sd_id, params in sd_data.items():
            # Look for common security event fields
            if "src" in params:
                entry.src_ip = params["src"]
            if "dst" in params:
                entry.dst_ip = params["dst"]
            if "spt" in params:
                try:
                    entry.src_port = int(params["spt"])
                except (ValueError, TypeError):
                    pass
            if "dpt" in params:
                try:
                    entry.dst_port = int(params["dpt"])
                except (ValueError, TypeError):
                    pass
            if "proto" in params:
                entry.protocol = params["proto"]
            if "act" in params:
                entry.action = params["act"]

    @property
    def stats(self) -> dict[str, int]:
        """Get parser statistics."""
        return {
            "rfc3164_parsed": self._parse_rfc3164_count,
            "rfc5424_parsed": self._parse_rfc5424_count,
        }
