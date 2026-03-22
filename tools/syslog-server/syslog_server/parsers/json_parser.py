"""
JSON log parser.

Parses log messages in JSON format, validating fields and mapping them
to the standard LogEntry structure.
"""

import json
from datetime import datetime
from typing import Any

import structlog

from syslog_server.parsers.base import BaseParser, ParseResult, ParserConfig
from syslog_server.storage.models import LogEntry
from syslog_server.utils.metrics import metrics


logger = structlog.get_logger(__name__)


class JSONParser(BaseParser):
    """
    Parser for JSON-formatted log messages.

    Supports various JSON log formats from different vendors and
    maps fields to the standard LogEntry structure.
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize the JSON parser."""
        super().__init__(config)
        self._parse_count = 0
        self._validation_error_count = 0

        # Field mapping configuration for common JSON log formats
        self._field_mappings = {
            # Common timestamp fields
            "timestamp": ["timestamp", "time", "@timestamp", "_time", "datetime", "date"],
            # Device information
            "device_ip": ["device_ip", "src_ip", "host_ip", "ip", "deviceAddress"],
            "device_type": ["device_type", "device_type", "log_type", "type", "category"],
            "device_hostname": ["device_hostname", "hostname", "host", "device_name", "deviceName"],
            "vendor": ["vendor", "manufacturer", "brand"],
            "model": ["model", "device_model", "product"],
            # Event information
            "event_type": ["event_type", "event_type", "type", "event_name", "action"],
            "event_category": ["event_category", "category", "log_category"],
            "severity": ["severity", "level", "priority", "log_level", "loglevel"],
            "event_code": ["event_code", "event_id", "code", "event_code", "message_id"],
            "message": ["message", "msg", "text", "description", "log_message"],
            # Network information
            "src_ip": ["src_ip", "source_ip", "sourceAddress", "sourceIP"],
            "src_port": ["src_port", "source_port", "sourcePort", "sourcePort"],
            "dst_ip": ["dst_ip", "dest_ip", "destination_ip", "destinationAddress", "destIP"],
            "dst_port": ["dst_port", "dest_port", "destination_port", "destinationPort", "destPort"],
            "protocol": ["protocol", "proto", "transport"],
            # Geo information
            "src_geo_country": ["src_geo_country", "country", "src_country", "source_country"],
            "src_geo_city": ["src_geo_city", "city", "src_city", "source_city"],
            # Threat information
            "action": ["action", "act", "decision"],
            "threat_id": ["threat_id", "threat", "threat_name", "malware"],
            "attack_pattern": ["attack_pattern", "attack", "technique", "mitre_technique"],
            "risk_score": ["risk_score", "risk", "severity_code"],
        }

    def can_parse(self, message: str) -> bool:
        """Check if message is valid JSON."""
        if not message:
            return False
        message = message.strip()
        # Quick check for JSON structure
        return (message.startswith("{") and message.endswith("}")) or (
            message.startswith("[") and message.endswith("]")
        )

    def parse(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Parse a JSON log message."""
        try:
            data = json.loads(message.strip())

            # Handle array of log entries
            if isinstance(data, list):
                if not data:
                    metrics.parse_errors.labels(parser=self.name, error_type="empty_array").inc()
                    return None
                # Parse first element
                data = data[0]

            if not isinstance(data, dict):
                metrics.parse_errors.labels(parser=self.name, error_type="invalid_json_type").inc()
                return None

            # Create log entry
            entry = self._create_entry(data, message, source_ip, received_at)

            self._parse_count += 1
            metrics.messages_parsed.labels(parser=self.name, status="success").inc()

            return entry

        except json.JSONDecodeError as e:
            logger.debug("Failed to parse JSON", error=str(e), message=message[:100])
            metrics.parse_errors.labels(parser=self.name, error_type="json_decode").inc()
            return None
        except Exception as e:
            logger.warning("Failed to process JSON message", error=str(e), message=message[:100])
            metrics.messages_parsed.labels(parser=self.name, status="error").inc()
            metrics.parse_errors.labels(parser=self.name, error_type="process_error").inc()
            return None

    def _create_entry(
        self,
        data: dict[str, Any],
        raw_message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> LogEntry:
        """Create a LogEntry from JSON data."""
        from syslog_server.storage.models import LogEntry

        # Create base entry
        entry = self.create_base_entry(
            message=self._extract_string(data, "message") or "",
            source_ip=source_ip,
            received_at=received_at,
        )

        # Extract timestamp
        timestamp = self._extract_timestamp(data)
        if timestamp:
            entry.timestamp = timestamp

        # Extract device information
        entry.device_type = self._extract_string(data, "device_type") or "json"
        entry.device_hostname = self._extract_string(data, "device_hostname") or None
        entry.vendor = self._extract_string(data, "vendor") or None
        entry.model = self._extract_string(data, "model") or None

        # Extract event information
        entry.event_type = self._extract_string(data, "event_type") or None
        entry.event_category = self._extract_string(data, "event_category") or None
        entry.event_code = self._extract_string(data, "event_code") or None

        # Extract severity
        severity = self._extract_severity(data)
        if severity is not None:
            entry.severity = severity
            _, entry.severity_label = self.severity_from_priority(severity)

        # Extract network information
        entry.src_ip = self._extract_string(data, "src_ip") or None
        entry.src_port = self._extract_int(data, "src_port") or None
        entry.dst_ip = self._extract_string(data, "dst_ip") or None
        entry.dst_port = self._extract_int(data, "dst_port") or None
        entry.protocol = self._extract_string(data, "protocol") or None

        # Extract geo information
        entry.src_geo_country = self._extract_string(data, "src_geo_country") or None
        entry.src_geo_city = self._extract_string(data, "src_geo_city") or None

        # Extract threat information
        entry.action = self._extract_string(data, "action") or None
        entry.threat_id = self._extract_string(data, "threat_id") or None
        entry.attack_pattern = self._extract_string(data, "attack_pattern") or None
        entry.risk_score = self._extract_int(data, "risk_score") or None

        # Store original JSON as parsed data
        entry.parsed_data = {
            "format": "json",
            "original_data": data,
        }

        return entry

    def _extract_string(self, data: dict[str, Any], field_name: str) -> str | None:
        """Extract a string field from JSON data using field mappings."""
        if field_name not in self._field_mappings:
            return None

        for key in self._field_mappings[field_name]:
            if key in data:
                value = data[key]
                if value is None:
                    continue
                # Convert to string if not already
                if isinstance(value, (int, float, bool)):
                    return str(value)
                if isinstance(value, str):
                    return value if value.strip() else None

        return None

    def _extract_int(self, data: dict[str, Any], field_name: str) -> int | None:
        """Extract an integer field from JSON data."""
        if field_name not in self._field_mappings:
            return None

        for key in self._field_mappings[field_name]:
            if key in data:
                value = data[key]
                if value is None:
                    continue
                try:
                    return int(value)
                except (ValueError, TypeError):
                    continue

        return None

    def _extract_timestamp(self, data: dict[str, Any]) -> datetime | None:
        """Extract and parse timestamp from JSON data."""
        timestamp_fields = self._field_mappings["timestamp"]

        for key in timestamp_fields:
            if key not in data:
                continue

            value = data[key]
            if value is None:
                continue

            # Already a datetime object
            if isinstance(value, datetime):
                return value

            # Unix timestamp (int or float)
            if isinstance(value, (int, float)):
                try:
                    # Check if it's in seconds or milliseconds
                    if value > 1_000_000_000_000:  # Milliseconds
                        value = value / 1000
                    return datetime.fromtimestamp(value)
                except (ValueError, OSError):
                    continue

            # String timestamp
            if isinstance(value, str):
                timestamp = self._parse_timestamp_string(value)
                if timestamp:
                    return timestamp

        return None

    def _parse_timestamp_string(self, timestamp_str: str) -> datetime | None:
        """Parse a timestamp string in various formats."""
        # Common timestamp formats
        formats = [
            # ISO 8601 formats
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            # Common log formats
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S %z",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %H:%M:%S",  # Syslog style (no year)
            # Other formats
            "%Y/%m/%d %H:%M:%S",
            "%Y%m%d %H%M%S",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp_str, fmt)
                # Handle year-less timestamps (syslog style)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed
            except ValueError:
                continue

        return None

    def _extract_severity(self, data: dict[str, Any]) -> int | None:
        """Extract and normalize severity from JSON data."""
        severity_fields = self._field_mappings["severity"]

        for key in severity_fields:
            if key not in data:
                continue

            value = data[key]
            if value is None:
                continue

            # Integer severity (0-7)
            if isinstance(value, int):
                if 0 <= value <= 7:
                    return value

            # String severity
            if isinstance(value, str):
                return self._parse_severity_string(value)

        return None

    def _parse_severity_string(self, severity_str: str) -> int | None:
        """Parse a severity string to syslog severity level."""
        severity_map = {
            # Emergency/Critical
            "emergency": 0,
            "emerg": 0,
            "critical": 2,
            "crit": 2,
            "fatal": 0,
            "panic": 0,
            # Error
            "error": 3,
            "err": 3,
            # Warning
            "warning": 4,
            "warn": 4,
            # Notice
            "notice": 5,
            # Info
            "information": 6,
            "info": 6,
            "informational": 6,
            # Debug
            "debug": 7,
            "trace": 7,
        }

        lower_str = severity_str.lower().strip()
        return severity_map.get(lower_str)

    def validate_fields(self, data: dict[str, Any]) -> bool:
        """
        Validate required fields in JSON data.

        Args:
            data: Parsed JSON data

        Returns:
            True if validation passes
        """
        # Check for minimum required fields
        has_message = any(key in data for key in self._field_mappings["message"])
        has_timestamp = any(key in data for key in self._field_mappings["timestamp"])

        if not has_message:
            self._validation_error_count += 1
            logger.debug("JSON validation failed: missing message field")
            return False

        return True

    @property
    def stats(self) -> dict[str, int]:
        """Get parser statistics."""
        return {
            "parsed": self._parse_count,
            "validation_errors": self._validation_error_count,
        }
