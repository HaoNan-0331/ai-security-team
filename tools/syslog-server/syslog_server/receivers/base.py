"""
Base receiver class for syslog receivers.

Defines the interface and common functionality for all receiver types.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable

import structlog

from syslog_server.storage.models import LogEntry
from syslog_server.utils.metrics import messages_received_total


logger = structlog.get_logger(__name__)


@dataclass
class ReceiverConfig:
    """Configuration for a receiver.

    Attributes:
        name: Unique name for this receiver
        protocol: Protocol type (udp/tcp)
        host: Host address to bind to
        port: Port to listen on
        format: Log format (rfc5424/rfc3164/cef/json)
        enabled: Whether this receiver is enabled
        workers: Number of worker tasks for processing
        buffer_size: Buffer size for socket operations
        max_connections: Maximum concurrent connections (TCP only)
        parser_options: Additional options for the parser
        description: Human-readable description
    """

    name: str
    protocol: str
    host: str
    port: int
    format: str
    enabled: bool = True
    workers: int = 4
    buffer_size: int = 1048576  # 1MB default
    max_connections: int = 1000
    parser_options: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def bind_address(self) -> tuple[str, int]:
        """Get the bind address as a tuple."""
        return (self.host, self.port)

    @property
    def label(self) -> str:
        """Get a label for metrics/logging."""
        return f"{self.protocol}_{self.name}"


@dataclass
class ReceivedMessage:
    """A received syslog message.

    Attributes:
        raw_data: Raw message bytes
        data: Decoded message string
        source: Source address (host, port)
        received_at: Timestamp when message was received
        receiver_name: Name of the receiver that received this message
    """

    raw_data: bytes
    data: str
    source: tuple[str, int]
    received_at: datetime
    receiver_name: str


class BaseReceiver(ABC):
    """Base class for all syslog receivers.

    Provides common functionality and defines the interface that
    all receivers must implement.
    """

    def __init__(self, config: ReceiverConfig):
        """Initialize the receiver.

        Args:
            config: Receiver configuration
        """
        self.config = config
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._message_handlers: list[Callable[[ReceivedMessage], Awaitable[None]]] = []
        self._logger = logger.bind(
            receiver=config.name,
            protocol=config.protocol,
            port=config.port,
        )

    @property
    def is_running(self) -> bool:
        """Check if the receiver is running."""
        return self._running

    @property
    def name(self) -> str:
        """Get the receiver name."""
        return self.config.name

    def add_message_handler(self, handler: Callable[[ReceivedMessage], Awaitable[None]]) -> None:
        """Add a message handler callback.

        Args:
            handler: Async function to call with received messages
        """
        if handler not in self._message_handlers:
            self._message_handlers.append(handler)

    def remove_message_handler(self, handler: Callable[[ReceivedMessage], Awaitable[None]]) -> None:
        """Remove a message handler callback.

        Args:
            handler: Handler function to remove
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    async def _handle_message(self, message: ReceivedMessage) -> None:
        """Handle a received message by passing to all registered handlers.

        Args:
            message: The received message
        """
        # Update metrics
        messages_received_total.labels(
            receiver=self.config.name,
            protocol=self.config.protocol,
            format=self.config.format,
        ).inc()

        self._logger.debug(
            "Message received",
            source=message.source[0],
            source_port=message.source[1],
            length=len(message.raw_data),
        )

        # Call all handlers
        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as e:
                self._logger.error(
                    "Handler failed",
                    handler=handler.__name__,
                    error=str(e),
                )

    async def start(self) -> None:
        """Start the receiver.

        Creates and starts the listener tasks.
        """
        if self._running:
            self._logger.warning("Receiver already running")
            return

        self._logger.info(
            "Starting receiver",
            host=self.config.host,
            port=self.config.port,
            format=self.config.format,
        )

        self._running = True

        # Start listener tasks
        try:
            await self._start_listener()
        except Exception as e:
            self._logger.error("Failed to start receiver", error=str(e))
            self._running = False
            raise

    async def stop(self) -> None:
        """Stop the receiver.

        Cancels all running tasks and closes the socket.
        """
        if not self._running:
            return

        self._logger.info("Stopping receiver")

        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete (with timeout)
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                self._logger.warning("Some tasks did not stop gracefully")

        self._tasks.clear()

        # Close the socket
        await self._close_socket()

        self._logger.info("Receiver stopped")

    @abstractmethod
    async def _start_listener(self) -> None:
        """Start the socket listener.

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def _close_socket(self) -> None:
        """Close the socket.

        Must be implemented by subclasses.
        """
        pass

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the receiver.

        Returns:
            Dictionary containing receiver status information
        """
        return {
            "name": self.config.name,
            "protocol": self.config.protocol,
            "host": self.config.host,
            "port": self.config.port,
            "format": self.config.format,
            "enabled": self.config.enabled,
            "running": self._running,
            "description": self.config.description,
        }


class ReceiverError(Exception):
    """Base exception for receiver errors."""

    pass


class ReceiverStartError(ReceiverError):
    """Exception raised when a receiver fails to start."""

    pass


class ReceiverStopError(ReceiverError):
    """Exception raised when a receiver fails to stop."""

    pass


class MessageParseError(ReceiverError):
    """Exception raised when message parsing fails."""

    pass
