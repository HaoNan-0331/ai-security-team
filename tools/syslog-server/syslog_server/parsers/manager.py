"""
Parser manager for handling multiple log formats.

Manages parser loading, format detection, and chain-based parsing.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import yaml

from syslog_server.parsers.base import BaseParser, ParserConfig, ParseResult
from syslog_server.parsers.syslog_parser import SyslogParser
from syslog_server.parsers.cef_parser import CEFParser
from syslog_server.parsers.json_parser import JSONParser
from syslog_server.config import settings
from syslog_server.utils.metrics import metrics


logger = structlog.get_logger(__name__)


# Built-in parser classes
BUILTIN_PARSERS = {
    "syslog": SyslogParser,
    "cef": CEFParser,
    "json": JSONParser,
}


class ParserManager:
    """
    Manager for log parsers.

    Handles parser loading from configuration, automatic format detection,
    and chain-based parsing where multiple parsers are tried in order.
    """

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the parser manager.

        Args:
            config_path: Path to parser configuration file (YAML)
        """
        self._parsers: list[BaseParser] = []
        self._parser_map: dict[str, BaseParser] = {}
        self._format_detectors: dict[str, re.Pattern] = {}

        # Initialize format detectors
        self._init_format_detectors()

        # Load configuration
        config_path = config_path or settings.parser_config_path
        self._load_config(config_path)

        # Load built-in parsers as fallback
        self._load_builtin_parsers()

        logger.info(
            "Parser manager initialized",
            parser_count=len(self._parsers),
            parsers=[p.name for p in self._parsers],
        )

    def _init_format_detectors(self) -> None:
        """Initialize regex patterns for format detection."""
        self._format_detectors = {
            "cef": re.compile(r"^CEF:\d+\|"),  # CEF format
            "json": re.compile(r"^\s*\{"),  # JSON object
            "syslog": re.compile(r"^<\d{1,3}>"),  # Syslog priority
        }

    def _load_config(self, config_path: str) -> None:
        """
        Load parser configuration from YAML file.

        Args:
            config_path: Path to configuration file
        """
        config_file = Path(config_path)

        if not config_file.exists():
            logger.info("Parser config not found, using defaults", path=config_path)
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            parsers_config = config.get("parsers", {})

            for name, parser_config in parsers_config.items():
                if not parser_config.get("enabled", True):
                    continue

                parser_cfg = ParserConfig(
                    enabled=parser_config.get("enabled", True),
                    priority=parser_config.get("priority", 100),
                    strict_mode=parser_config.get("strict_mode", False),
                    default_tags=parser_config.get("default_tags", []),
                    default_severity=parser_config.get("default_severity", 6),
                )

                # Get parser class
                parser_class = BUILTIN_PARSERS.get(name)
                if parser_class:
                    parser = parser_class(config=parser_cfg)
                    self._add_parser(parser)
                else:
                    logger.warning("Unknown parser type in config", name=name)

        except Exception as e:
            logger.error("Failed to load parser config", error=str(e), path=config_path)

    def _load_builtin_parsers(self) -> None:
        """Load built-in parsers with default configuration."""
        default_config = ParserConfig()

        for name, parser_class in BUILTIN_PARSERS.items():
            if name not in self._parser_map:
                parser = parser_class(config=default_config)
                self._add_parser(parser)

    def _add_parser(self, parser: BaseParser) -> None:
        """Add a parser to the manager."""
        self._parsers.append(parser)
        self._parser_map[parser.name] = parser

        # Sort by priority (lower = higher priority)
        self._parsers.sort(key=lambda p: p.config.priority)

    def detect_format(self, message: str) -> str | None:
        """
        Detect the format of a log message.

        Args:
            message: Raw log message

        Returns:
            Format name or None if unknown
        """
        for format_name, pattern in self._format_detectors.items():
            if pattern.match(message.strip()):
                return format_name
        return None

    def parse(
        self,
        message: str,
        source_ip: str,
        received_at: datetime | None = None,
        format_hint: str | None = None,
    ) -> ParseResult:
        """
        Parse a log message using available parsers.

        Tries parsers in priority order until one succeeds.

        Args:
            message: Raw log message
            source_ip: IP address of the source device
            received_at: When the message was received
            format_hint: Optional hint about the message format

        Returns:
            LogEntry if parsing succeeded, None otherwise
        """
        if not message:
            return None

        # Track total parse attempts
        parse_attempts = 0

        # Try format-specific parser if hint provided
        if format_hint and format_hint in self._parser_map:
            parser = self._parser_map[format_hint]
            parse_attempts += 1
            result = parser.parse_safe(message, source_ip, received_at)
            if result:
                metrics.messages_received.labels(
                    receiver="parser_manager",
                    protocol=format_hint,
                    format=format_hint,
                ).inc()
                return result

        # Detect format if no hint or hint failed
        detected_format = self.detect_format(message)
        if detected_format and detected_format in self._parser_map:
            parser = self._parser_map[detected_format]
            parse_attempts += 1
            result = parser.parse_safe(message, source_ip, received_at)
            if result:
                metrics.messages_received.labels(
                    receiver="parser_manager",
                    protocol=detected_format,
                    format=detected_format,
                ).inc()
                return result

        # Try all parsers in priority order
        for parser in self._parsers:
            # Skip already tried parsers
            if parser.name in (format_hint, detected_format):
                continue

            parse_attempts += 1
            result = parser.parse_safe(message, source_ip, received_at)
            if result:
                metrics.messages_received.labels(
                    receiver="parser_manager",
                    protocol="unknown",
                    format=parser.name,
                ).inc()
                return result

        # All parsers failed
        logger.debug(
            "Failed to parse message",
            message=message[:100],
            attempts=parse_attempts,
        )
        metrics.parse_errors.labels(parser="manager", error_type="no_parser").inc()

        return None

    def parse_batch(
        self,
        messages: list[tuple[str, str]],
        received_at: datetime | None = None,
    ) -> list[ParseResult]:
        """
        Parse multiple messages in batch.

        Args:
            messages: List of (message, source_ip) tuples
            received_at: When the messages were received

        Returns:
            List of LogEntry objects (None for failed parses)
        """
        results = []
        for message, source_ip in messages:
            result = self.parse(message, source_ip, received_at)
            results.append(result)
        return results

    def get_parser(self, name: str) -> BaseParser | None:
        """Get a parser by name."""
        return self._parser_map.get(name)

    def get_parser_stats(self) -> dict[str, Any]:
        """Get statistics from all parsers."""
        stats = {
            "parsers": {},
            "total_parsers": len(self._parsers),
        }

        for parser in self._parsers:
            parser_stats = getattr(parser, "stats", None)
            if parser_stats:
                stats["parsers"][parser.name] = dict(parser_stats)
            else:
                stats["parsers"][parser.name] = {"enabled": parser.config.enabled}

        return stats

    def reload_config(self, config_path: str | None = None) -> None:
        """Reload parser configuration."""
        config_path = config_path or settings.parser_config_path

        # Clear existing parsers
        self._parsers.clear()
        self._parser_map.clear()

        # Reload configuration
        self._load_config(config_path)
        self._load_builtin_parsers()

        logger.info("Parser configuration reloaded", path=config_path)


# Global parser manager instance
_parser_manager: ParserManager | None = None


def get_parser_manager(config_path: str | None = None) -> ParserManager:
    """
    Get the global parser manager instance.

    Args:
        config_path: Optional path to parser configuration file

    Returns:
        ParserManager instance
    """
    global _parser_manager

    if _parser_manager is None:
        _parser_manager = ParserManager(config_path)

    return _parser_manager


def reload_parser_manager(config_path: str | None = None) -> ParserManager:
    """
    Reload the global parser manager.

    Args:
        config_path: Optional path to parser configuration file

    Returns:
        New ParserManager instance
    """
    global _parser_manager
    _parser_manager = ParserManager(config_path)
    return _parser_manager
