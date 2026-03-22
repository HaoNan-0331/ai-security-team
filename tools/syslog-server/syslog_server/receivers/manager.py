"""
Receiver manager for syslog server.

Manages loading, starting, and stopping all configured receivers.
Coordinates message flow from receivers to storage.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

import structlog
import yaml

from syslog_server.config import settings
from syslog_server.receivers.base import (
    BaseReceiver,
    ReceiverConfig,
    ReceivedMessage,
)
from syslog_server.receivers.udp_receiver import UDPReceiver, BatchUDPReceiver
from syslog_server.receivers.tcp_receiver import TCPReceiver, TLSTCPReceiver
from syslog_server.storage.models import LogEntry
from syslog_server.storage.manager import StorageManager
from syslog_server.utils.metrics import (
    messages_received_total,
    messages_stored_total,
    parse_errors_total,
)


logger = structlog.get_logger(__name__)


@dataclass
class ReceiverStatus:
    """Status of a single receiver.

    Attributes:
        name: Receiver name
        protocol: Protocol type
        running: Whether the receiver is running
        enabled: Whether the receiver is enabled
        connections: Number of active connections (TCP only)
        messages_received: Total messages received
        last_message_time: Time of last received message
    """

    name: str
    protocol: str
    running: bool
    enabled: bool
    connections: int = 0
    messages_received: int = 0
    last_message_time: datetime | None = None


class ReceiverManager:
    """Manager for all syslog receivers.

    Handles:
    - Loading receiver configuration from YAML
    - Creating receiver instances
    - Starting/stopping all receivers
    - Routing messages to storage
    - Collecting receiver status
    """

    def __init__(self, storage_manager: StorageManager) -> None:
        """Initialize the receiver manager.

        Args:
            storage_manager: Storage manager for persisting messages
        """
        self._storage = storage_manager
        self._receivers: dict[str, BaseReceiver] = {}
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=50000)
        self._processor_task: asyncio.Task | None = None
        self._stats: dict[str, dict[str, Any]] = {}

    async def load_config(self, config_path: str | None = None) -> None:
        """Load receiver configuration from YAML file.

        Args:
            config_path: Path to config file (uses default if not specified)
        """
        if config_path is None:
            # Check if the configured path exists
            config_file = Path(settings.receiver_config_path)
            if not config_file.exists():
                # Try relative to config directory
                config_file = settings.config_dir / "receivers.yaml"
            config_path = str(config_file)

        self._logger = logger.bind(component="receiver_manager")
        self._logger.info("Loading receiver configuration", path=config_path)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data or "receivers" not in config_data:
                self._logger.warning("No receivers configured")
                return

            # Create receiver instances
            for receiver_config in config_data["receivers"]:
                config = ReceiverConfig(**receiver_config)

                # Skip disabled receivers
                if not config.enabled:
                    self._logger.debug("Skipping disabled receiver", name=config.name)
                    continue

                await self._create_receiver(config)

            self._logger.info(
                "Receivers loaded",
                total=len(self._receivers),
                receivers=list(self._receivers.keys()),
            )

        except Exception as e:
            self._logger.error("Failed to load receiver configuration", error=str(e))
            raise

    async def _create_receiver(self, config: ReceiverConfig) -> None:
        """Create a receiver instance based on configuration.

        Args:
            config: Receiver configuration
        """
        self._logger.debug(
            "Creating receiver",
            name=config.name,
            protocol=config.protocol,
        )

        receiver: BaseReceiver

        if config.protocol == "udp":
            # Use batch receiver for better performance
            receiver = BatchUDPReceiver(
                config,
                batch_size=100,
                batch_timeout=0.1,
            )
        elif config.protocol == "tcp":
            receiver = TCPReceiver(config)
        elif config.protocol == "tls":
            # TLS requires additional config - use regular TCP for now
            # In production, you would load cert paths from config
            receiver = TCPReceiver(config)
        else:
            self._logger.warning(
                "Unknown protocol, skipping",
                name=config.name,
                protocol=config.protocol,
            )
            return

        # Register message handler
        receiver.add_message_handler(self._handle_raw_message)

        # Initialize stats
        self._stats[config.name] = {
            "messages_received": 0,
            "last_message_time": None,
        }

        self._receivers[config.name] = receiver

    async def start(self) -> None:
        """Start all enabled receivers."""
        if self._running:
            self._logger.warning("Receiver manager already running")
            return

        self._logger.info("Starting receiver manager")

        self._running = True

        # Start message processor task
        self._processor_task = asyncio.create_task(
            self._process_messages(),
            name="receiver-message-processor",
        )

        # Start all receivers
        start_tasks = []
        for receiver in self._receivers.values():
            task = asyncio.create_task(receiver.start())
            start_tasks.append(task)

        # Wait for all receivers to start
        results = await asyncio.gather(*start_tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                receiver_name = list(self._receivers.keys())[i]
                self._logger.error(
                    "Receiver failed to start",
                    receiver=receiver_name,
                    error=str(result),
                )

        self._logger.info("Receiver manager started")

    async def stop(self) -> None:
        """Stop all receivers."""
        if not self._running:
            return

        self._logger.info("Stopping receiver manager")

        self._running = False

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await asyncio.wait_for(self._processor_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        # Stop all receivers
        stop_tasks = []
        for receiver in self._receivers.values():
            task = asyncio.create_task(receiver.stop())
            stop_tasks.append(task)

        await asyncio.gather(*stop_tasks, return_exceptions=True)

        self._logger.info("Receiver manager stopped")

    async def _handle_raw_message(self, message: ReceivedMessage) -> None:
        """Handle a raw received message.

        Args:
            message: The received message
        """
        # Update stats
        if message.receiver_name in self._stats:
            self._stats[message.receiver_name]["messages_received"] += 1
            self._stats[message.receiver_name]["last_message_time"] = message.received_at

        # Put in processing queue
        try:
            self._message_queue.put_nowait(message)
        except asyncio.QueueFull:
            self._logger.warning(
                "Message processing queue full, dropping message",
                receiver=message.receiver_name,
                source=message.source[0],
            )

    async def _process_messages(self) -> None:
        """Background task to process messages from the queue."""
        self._logger.debug("Message processor started")

        while self._running:
            try:
                # Get message with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0,
                )

                # Parse and store message
                await self._parse_and_store(message)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Message processing error", error=str(e))

        self._logger.debug("Message processor stopped")

    async def _parse_and_store(self, message: ReceivedMessage) -> None:
        """Parse and store a received message.

        Args:
            message: The received message to process
        """
        try:
            # Create a basic log entry
            # In production, you would use a parser module here
            log_entry = LogEntry(
                received_at=message.received_at,
                timestamp=message.received_at,
                device_ip=message.source[0],
                device_type="unknown",
                severity=6,  # Default to info
                severity_label="info",
                message=message.data,
                raw_message=message.raw_data.decode("utf-8", errors="replace"),
            )

            # Store in database
            log_id = await self._storage.store_log(log_entry)

            if log_id:
                messages_stored_total.labels(backend="database", status="success").inc()
                self._logger.debug(
                    "Log stored",
                    log_id=log_id,
                    source=message.source[0],
                )
            else:
                messages_stored_total.labels(backend="database", status="error").inc()

        except Exception as e:
            self._logger.error(
                "Failed to parse/store message",
                error=str(e),
                source=message.source[0],
            )
            parse_errors_total.labels(
                parser="receiver_manager",
                error_type=type(e).__name__,
            ).inc()

    def get_status(self) -> list[dict[str, Any]]:
        """Get the status of all receivers.

        Returns:
            List of receiver status dictionaries
        """
        statuses = []

        for receiver in self._receivers.values():
            status = receiver.get_status()
            # Add stats
            if receiver.name in self._stats:
                status["messages_received"] = self._stats[receiver.name]["messages_received"]
                status["last_message_time"] = self._stats[receiver.name]["last_message_time"]
            statuses.append(status)

        return statuses

    def get_receiver(self, name: str) -> BaseReceiver | None:
        """Get a receiver by name.

        Args:
            name: Receiver name

        Returns:
            Receiver instance or None if not found
        """
        return self._receivers.get(name)

    async def reload_config(self, config_path: str | None = None) -> None:
        """Reload receiver configuration.

        Args:
            config_path: Path to config file (uses default if not specified)
        """
        self._logger.info("Reloading receiver configuration")

        # Stop all receivers
        await self.stop()

        # Clear existing receivers
        self._receivers.clear()
        self._stats.clear()

        # Load new configuration
        await self.load_config(config_path)

        # Start receivers
        await self.start()

        self._logger.info("Receiver configuration reloaded")

    @property
    def queue_size(self) -> int:
        """Get the current message queue size."""
        return self._message_queue.qsize()

    @property
    def receivers_count(self) -> int:
        """Get the number of configured receivers."""
        return len(self._receivers)

    @property
    def running_receivers_count(self) -> int:
        """Get the number of running receivers."""
        return sum(1 for r in self._receivers.values() if r.is_running)
