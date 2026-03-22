"""
CEF (Common Event Format) parser.

Parses log messages in CEF format, commonly used by security devices
like firewalls, IDS/IPS, and SIEM systems.
"""

import re
from datetime import datetime
from typing import Any
from urllib.parse import unquote

import structlog

from syslog_server.parsers.base import BaseParser, ParseResult, ParserConfig
from syslog_server.storage.models import LogEntry
from syslog_server.utils.metrics import metrics


logger = structlog.get_logger(__name__)


# CEF Header pattern: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity
CEF_HEADER_PATTERN = re.compile(
    r"""^
    CEF:(?P<cef_version>\d+)\|
    (?P<vendor>[^|]*)\|
    (?P<product>[^|]*)\|
    (?P<device_version>[^|]*)\|
    (?P<signature_id>[^|]*)\|
    (?P<name>[^|]*)\|
    (?P<severity>\d+)\|
    """,
    re.VERBOSE,
)

# CEF Extension pattern: key=value pairs
# Simple pattern for key=value matching
CEF_EXTENSION_PATTERN = re.compile(r'([\w.]+)=([\w\-\.:/]+)')


class CEFParser(BaseParser):
    """
    Parser for CEF (Common Event Format) messages.

    CEF format:
    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension

    Extension format: key1=value1 key2=value2 ...
    """

    # CEF header start detection
    CEF_PREFIX_PATTERN = re.compile(r"^CEF:\d+\|")

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize the CEF parser."""
        super().__init__(config)
        self._parse_count = 0
        self._header_only_count = 0

    def can_parse(self, message: str) -> bool:
        """Check if message is in CEF format."""
        if not message:
            return False
        return bool(self.CEF_PREFIX_PATTERN.match(message.strip()))

    def parse(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> ParseResult:
        """Parse a CEF message."""
        try:
            message = message.strip()
            header_match = CEF_HEADER_PATTERN.match(message)

            if not header_match:
                metrics.parse_errors.labels(parser=self.name, error_type="invalid_header").inc()
                return None

            # Parse header
            header_end = header_match.end()
            header_data = header_match.groupdict()
            extension_str = message[header_end:] if header_end < len(message) else ""

            # Parse extensions
            extensions = self._parse_extensions(extension_str)

            # Create log entry
            entry = self._create_entry(header_data, extensions, message, source_ip, received_at)

            self._parse_count += 1
            metrics.messages_parsed.labels(parser=self.name, status="success").inc()

            return entry

        except Exception as e:
            logger.warning("Failed to parse CEF message", error=str(e), message=message[:100])
            metrics.messages_parsed.labels(parser=self.name, status="error").inc()
            metrics.parse_errors.labels(parser=self.name, error_type="parse_error").inc()
            return None

    def _parse_extensions(self, extension_str: str) -> dict[str, str]:
        """
        Parse CEF extension key-value pairs.

        Handles:
        - Simple key=value pairs
        - Quoted values with spaces
        - URL-encoded values
        - Values containing pipe characters
        """
        extensions = {}

        if not extension_str or extension_str.strip() == "-":
            return extensions

        # Custom parser to handle quoted values and special characters
        remaining = extension_str.strip()
        while remaining:
            # Find next key= (handles both quoted and unquoted values)
            match = re.match(r'([\w.]+)=(?:\"([^\"]*)\"|([^ \t]*))', remaining)
            if not match:
                break

            key = match.group(1)
            # Try quoted value first, then unquoted
            value = match.group(2) or match.group(3)

            # URL decode the value
            try:
                value = unquote(value)
            except Exception:
                pass

            extensions[key] = value

            # Move past this match
            remaining = remaining[match.end():].lstrip()

        return extensions

    def _create_entry(
        self,
        header_data: dict[str, str],
        extensions: dict[str, str],
        raw_message: str,
        source_ip: str,
        received_at: datetime | None = None,
    ) -> LogEntry:
        """Create a LogEntry from CEF header and extensions."""
        from syslog_server.storage.models import LogEntry

        # Parse severity from CEF (0-10 scale, map to syslog 0-7)
        cef_severity = int(header_data.get("severity", "0"))
        severity = self._map_cef_severity(cef_severity)
        _, severity_label = self.severity_from_priority(severity)

        # Create base entry
        entry = self.create_base_entry(
            message=header_data.get("name", ""),
            source_ip=source_ip,
            received_at=received_at,
        )

        # Update with header fields
        entry.vendor = header_data.get("vendor") or None
        entry.model = header_data.get("product") or None
        entry.device_type = header_data.get("product") or "cef"
        entry.severity = severity
        entry.severity_label = severity_label
        entry.event_code = header_data.get("signature_id") or None
        entry.message = header_data.get("name", "")

        # Build device hostname from available info
        device_vendor = header_data.get("vendor", "")
        device_product = header_data.get("product", "")
        if device_product:
            entry.device_hostname = f"{device_vendor}_{device_product}".lower().replace(" ", "_")

        # Parse extensions and populate fields
        self._populate_extensions(entry, extensions)

        # Store raw CEF data
        parsed_data = {
            "format": "cef",
            "cef_version": header_data.get("cef_version"),
            "device_version": header_data.get("device_version"),
            "cef_severity": cef_severity,
            "signature_id": header_data.get("signature_id"),
            "extensions": extensions,
        }
        entry.parsed_data = parsed_data

        return entry

    def _populate_extensions(self, entry: LogEntry, extensions: dict[str, str]) -> None:
        """Populate LogEntry fields from CEF extensions."""
        # Standard CEF field mappings
        field_mappings = {
            # Network fields
            "src": "src_ip",
            "dst": "dst_ip",
            "spt": "src_port",
            "dpt": "dst_port",
            "proto": "protocol",
            # Device information
            "dhost": "device_hostname",
            "dvchost": "device_hostname",
            # Event information
            "act": "action",
            "cn1Label": "event_type",  # Custom label, value in cn1
            "cn1": "event_code",  # Custom number
            # Threat information
            "threat": "threat_id",
            "cs1Label": "threat_id",  # Custom string label
            "cs1": "attack_pattern",  # Custom string value
            "cs2Label": "event_category",
            "cs2": "event_category",
        }

        # Direct field mappings
        for cef_field, entry_field in field_mappings.items():
            if cef_field in extensions:
                value = extensions[cef_field]
                # Handle port numbers
                if entry_field in ("src_port", "dst_port"):
                    try:
                        setattr(entry, entry_field, int(value))
                    except (ValueError, TypeError):
                        pass
                else:
                    setattr(entry, entry_field, value)

        # Parse custom fields (cn1-3, cs1-6)
        custom_number_fields = ["cn1", "cn2", "cn3"]
        for cn in custom_number_fields:
            if cn in extensions:
                label_key = f"{cn}Label"
                if label_key in extensions:
                    label = extensions[label_key]
                    value = extensions[cn]
                    if not entry.parsed_data:
                        entry.parsed_data = {}
                    entry.parsed_data[f"custom_{label}"] = value

        custom_string_fields = ["cs1", "cs2", "cs3", "cs4", "cs5", "cs6"]
        for cs in custom_string_fields:
            if cs in extensions:
                label_key = f"{cs}Label"
                if label_key in extensions:
                    label = extensions[label_key]
                    value = extensions[cs]
                    if not entry.parsed_data:
                        entry.parsed_data = {}
                    entry.parsed_data[f"custom_{label}"] = value

        # Geo location fields
        if "srcCountry" in extensions:
            entry.src_geo_country = extensions["srcCountry"]
        if "srcCity" in extensions:
            entry.src_geo_city = extensions["srcCity"]

        # Risk score
        if "risk" in extensions:
            try:
                entry.risk_score = int(extensions["risk"])
            except (ValueError, TypeError):
                pass

    def _map_cef_severity(self, cef_severity: int) -> int:
        """
        Map CEF severity (0-10) to syslog severity (0-7).

        CEF: 0=Low, 1-3=Medium, 4-6=High, 7-10=Very High
        Syslog: 0=Emerg, 1=Alert, 2=Crit, 3=Err, 4=Warning, 5=Notice, 6=Info, 7=Debug
        """
        severity_map = {
            0: 6,  # Low -> Info
            1: 5,  # Medium-Low -> Notice
            2: 4,  # Medium -> Warning
            3: 4,  # Medium -> Warning
            4: 3,  # High -> Error
            5: 3,  # High -> Error
            6: 2,  # High -> Critical
            7: 1,  # Very-High -> Alert
            8: 1,  # Very-High -> Alert
            9: 0,  # Very-High -> Emergency
            10: 0,  # Very-High -> Emergency
        }
        return severity_map.get(cef_severity, 6)

    @property
    def stats(self) -> dict[str, int]:
        """Get parser statistics."""
        return {
            "parsed": self._parse_count,
            "header_only": self._header_only_count,
        }
