"""
UDP receiver for syslog messages.

Implements an async UDP socket listener for receiving syslog messages
over UDP protocol (RFC5424/RFC3164).
"""

import asyncio
import socket
from datetime import datetime
from typing import Any

import structlog

from syslog_server.receivers.base import (
    BaseReceiver,
    ReceiverConfig,
    ReceivedMessage,
    ReceiverStartError,
)
from syslog_server.utils.metrics import messages_received_total


logger = structlog.get_logger(__name__)


class UDPReceiver(BaseReceiver):
    """UDP-based syslog receiver.

    Provides high-performance UDP message reception with support for:
    - Multiple concurrent worker tasks
    - Batch message processing
    - Configurable buffer sizes
    """

    def __init__(self, config: ReceiverConfig) -> None:
        """Initialize the UDP receiver.

        Args:
            config: Receiver configuration
        """
        super().__init__(config)
        self._socket: socket.socket | None = None
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: asyncio.DatagramProtocol | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._worker_tasks: list[asyncio.Task] = []

    async def _start_listener(self) -> None:
        """Start the UDP socket listener."""
        try:
            # Create UDP socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

            # Set buffer size
            self._socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                self.config.buffer_size,
            )

            # Bind to address
            try:
                self._socket.bind(self.config.bind_address)
            except OSError as e:
                raise ReceiverStartError(
                    f"Failed to bind to {self.config.host}:{self.config.port}: {e}"
                )

            self._logger.info(
                "UDP socket bound",
                fd=self._socket.fileno(),
                buffer_size=self.config.buffer_size,
            )

            # Create asyncio transport
            loop = asyncio.get_running_loop()
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: _UDPProtocol(
                    self._message_queue,
                    self.config,
                    self._logger,
                ),
                sock=self._socket,
            )

            # Start worker tasks
            for i in range(self.config.workers):
                task = asyncio.create_task(
                    self._worker(f"{self.config.name}-worker-{i}"),
                    name=f"{self.config.name}-worker-{i}",
                )
                self._worker_tasks.append(task)
                self._tasks.append(task)

            self._logger.info(
                "UDP receiver started",
                workers=self.config.workers,
            )

        except Exception as e:
            await self._close_socket()
            if isinstance(e, ReceiverStartError):
                raise
            raise ReceiverStartError(f"Failed to start UDP receiver: {e}")

    async def _close_socket(self) -> None:
        """Close the UDP socket."""
        # Cancel worker tasks first
        for task in self._worker_tasks:
            if not task.done():
                task.cancel()

        if self._worker_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._worker_tasks, return_exceptions=True),
                    timeout=2.0,
                )
            except asyncio.TimeoutError:
                pass

        self._worker_tasks.clear()

        # Close transport
        if self._transport:
            self._transport.close()
            try:
                await asyncio.wait_for(self._transport.wait_closed(), timeout=2.0)
            except asyncio.TimeoutError:
                pass
            self._transport = None

        # Close socket
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        self._protocol = None

    async def _worker(self, worker_name: str) -> None:
        """Worker task for processing received messages.

        Args:
            worker_name: Name of this worker for logging
        """
        worker_logger = self._logger.bind(worker=worker_name)
        worker_logger.debug("Worker started")

        while self._running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0,
                )

                # Process message
                await self._handle_message(message)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                worker_logger.debug("Worker cancelled")
                break
            except Exception as e:
                worker_logger.error("Worker error", error=str(e))

        worker_logger.debug("Worker stopped")

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the UDP receiver.

        Returns:
            Dictionary containing receiver status information
        """
        status = super().get_status()
        status.update({
            "queue_size": self._message_queue.qsize(),
            "queue_maxsize": self._message_queue.maxsize,
            "workers_active": len([t for t in self._worker_tasks if not t.done()]),
        })
        return status


class _UDPProtocol(asyncio.DatagramProtocol):
    """Protocol handler for UDP datagrams.

    Receives datagrams and puts them into the message queue for processing.
    """

    def __init__(
        self,
        message_queue: asyncio.Queue,
        config: ReceiverConfig,
        logger: structlog.stdlib.BoundLogger,
    ) -> None:
        """Initialize the UDP protocol.

        Args:
            message_queue: Queue to put received messages into
            config: Receiver configuration
            logger: Logger instance
        """
        self._queue = message_queue
        self._config = config
        self._logger = logger
        self._transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """Called when a connection is made."""
        self._transport = transport
        self._logger.debug("UDP protocol connected")

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection is lost or closed."""
        if exc:
            self._logger.error("UDP connection lost", error=str(exc))
        else:
            self._logger.debug("UDP connection closed")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Called when a datagram is received.

        Args:
            data: Received data bytes
            addr: Source address (host, port)
        """
        try:
            # Decode message
            try:
                message_text = data.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                message_text = data.decode("latin-1", errors="replace")

            # Create received message
            message = ReceivedMessage(
                raw_data=data,
                data=message_text,
                source=addr,
                received_at=datetime.now(),
                receiver_name=self._config.name,
            )

            # Put in queue (non-blocking, drop if full)
            try:
                self._queue.put_nowait(message)
            except asyncio.QueueFull:
                self._logger.warning(
                    "Message queue full, dropping message",
                    source=addr[0],
                    queue_size=self._queue.qsize(),
                )

        except Exception as e:
            self._logger.error("Failed to process datagram", error=str(e))

    def error_received(self, exc: Exception) -> None:
        """Called when a receive error occurs."""
        self._logger.error("UDP receive error", error=str(exc))


class BatchUDPReceiver(UDPReceiver):
    """UDP receiver with batch processing support.

    This receiver accumulates messages for a short period before
    processing them in batches, which can improve throughput
    for high-volume scenarios.
    """

    def __init__(
        self,
        config: ReceiverConfig,
        batch_size: int = 100,
        batch_timeout: float = 0.1,
    ) -> None:
        """Initialize the batch UDP receiver.

        Args:
            config: Receiver configuration
            batch_size: Maximum number of messages to batch
            batch_timeout: Maximum time to wait for a complete batch (seconds)
        """
        super().__init__(config)
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batch: list[ReceivedMessage] = []
        self._last_batch_time = datetime.now()
        self._batch_lock = asyncio.Lock()

    async def _worker(self, worker_name: str) -> None:
        """Worker task for batch processing received messages.

        Args:
            worker_name: Name of this worker for logging
        """
        worker_logger = self._logger.bind(worker=worker_name)
        worker_logger.debug("Batch worker started")

        while self._running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=self._batch_timeout,
                )

                # Add to batch
                async with self._batch_lock:
                    self._batch.append(message)

                    # Process batch if full or timeout
                    should_process = (
                        len(self._batch) >= self._batch_size or
                        (datetime.now() - self._last_batch_time).total_seconds() >= self._batch_timeout
                    )

                    if should_process:
                        batch = self._batch.copy()
                        self._batch.clear()
                        self._last_batch_time = datetime.now()

                # Process batch
                if should_process:
                    await self._process_batch(batch, worker_logger)

            except asyncio.TimeoutError:
                # Process any remaining messages in batch
                async with self._batch_lock:
                    if self._batch:
                        batch = self._batch.copy()
                        self._batch.clear()
                        self._last_batch_time = datetime.now()
                        await self._process_batch(batch, worker_logger)
                continue
            except asyncio.CancelledError:
                worker_logger.debug("Batch worker cancelled")
                break
            except Exception as e:
                worker_logger.error("Batch worker error", error=str(e))

        worker_logger.debug("Batch worker stopped")

    async def _process_batch(
        self,
        batch: list[ReceivedMessage],
        worker_logger: structlog.stdlib.BoundLogger,
    ) -> None:
        """Process a batch of messages.

        Args:
            batch: List of messages to process
            worker_logger: Logger instance
        """
        if not batch:
            return

        worker_logger.debug("Processing batch", batch_size=len(batch))

        # Update metrics for the batch
        messages_received_total.labels(
            receiver=self.config.name,
            protocol=self.config.protocol,
            format=self.config.format,
        ).inc(len(batch))

        # Process each message
        for message in batch:
            try:
                await self._handle_message(message)
            except Exception as e:
                worker_logger.error(
                    "Failed to handle message in batch",
                    error=str(e),
                    source=message.source[0],
                )
