"""
TCP receiver for syslog messages.

Implements an async TCP socket listener for receiving syslog messages
over TCP protocol (RFC5424/RFC3164).
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


class TCPReceiver(BaseReceiver):
    """TCP-based syslog receiver.

    Provides reliable TCP message reception with support for:
    - Multiple concurrent connections
    - Connection management and tracking
    - Message frame detection (octet-counting vs non-transparent)
    """

    def __init__(self, config: ReceiverConfig) -> None:
        """Initialize the TCP receiver.

        Args:
            config: Receiver configuration
        """
        super().__init__(config)
        self._server: asyncio.Server | None = None
        self._connections: dict[str, _TCPConnection] = {}
        self._connections_lock = asyncio.Lock()
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._worker_tasks: list[asyncio.Task] = []

    async def _start_listener(self) -> None:
        """Start the TCP socket listener."""
        try:
            # Create TCP server using start_server (Python 3.11+)
            async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
                """Handle incoming client connection."""
                addr = writer.get_extra_info("peername")
                connection_id = f"{addr[0]}:{addr[1]}-{id(writer)}"

                # Check connection limit
                async with self._connections_lock:
                    if len(self._connections) >= self.config.max_connections:
                        self._logger.warning(
                            "Max connections reached, rejecting",
                            connection_id=connection_id,
                            addr=addr[0],
                            current=len(self._connections),
                        )
                        writer.close()
                        await writer.wait_closed()
                        return

                    self._logger.debug(
                        "Connection opened",
                        connection_id=connection_id,
                        addr=addr[0],
                        port=addr[1],
                        total=len(self._connections) + 1,
                    )

                # Create connection handler
                conn = _TCPConnection(
                    reader=reader,
                    writer=writer,
                    addr=addr,
                    connection_id=connection_id,
                    config=self.config,
                    logger=self._logger,
                    message_queue=self._message_queue,
                )

                async with self._connections_lock:
                    self._connections[connection_id] = conn

                # Start connection reader
                await conn.start()

                await conn.close()

                async with self._connections_lock:
                    if connection_id in self._connections:
                        del self._connections[connection_id]

                self._logger.debug(
                    "Connection closed",
                    connection_id=connection_id,
                    addr=addr[0],
                    remaining=len(self._connections),
                )

            self._server = await asyncio.start_server(
                handle_client,
                host=self.config.host,
                port=self.config.port,
                reuse_address=True,
                reuse_port=True,
            )

            # Start serving
            await self._server.start_serving()

            # Start worker tasks
            for i in range(self.config.workers):
                task = asyncio.create_task(
                    self._worker(f"{self.config.name}-worker-{i}"),
                    name=f"{self.config.name}-worker-{i}",
                )
                self._worker_tasks.append(task)
                self._tasks.append(task)

            self._logger.info(
                "TCP receiver started",
                workers=self.config.workers,
                max_connections=self.config.max_connections,
            )

        except Exception as e:
            await self._close_socket()
            if isinstance(e, ReceiverStartError):
                raise
            raise ReceiverStartError(f"Failed to start TCP receiver: {e}")

    async def _close_socket(self) -> None:
        """Close the TCP server and all connections."""
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

        # Close server
        if self._server:
            self._server.close()
            try:
                await asyncio.wait_for(self._server.wait_closed(), timeout=2.0)
            except asyncio.TimeoutError:
                pass
            self._server = None

        # Close all connections
        async with self._connections_lock:
            for conn in list(self._connections.values()):
                await conn.close()
            self._connections.clear()

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

    async def _on_connection_open(self, connection_id: str, addr: tuple[str, int]) -> None:
        """Handle a new connection opening.

        Args:
            connection_id: Unique connection identifier
            addr: Remote address (host, port)
        """
        async with self._connections_lock:
            if len(self._connections) >= self.config.max_connections:
                self._logger.warning(
                    "Max connections reached, rejecting",
                    connection_id=connection_id,
                    addr=addr[0],
                    current=len(self._connections),
                )
                return False

            self._logger.debug(
                "Connection opened",
                connection_id=connection_id,
                addr=addr[0],
                port=addr[1],
                total=len(self._connections) + 1,
            )
            return True

    async def _on_connection_close(self, connection_id: str, addr: tuple[str, int]) -> None:
        """Handle a connection closing.

        Args:
            connection_id: Unique connection identifier
            addr: Remote address (host, port)
        """
        async with self._connections_lock:
            if connection_id in self._connections:
                del self._connections[connection_id]

        self._logger.debug(
            "Connection closed",
            connection_id=connection_id,
            addr=addr[0],
            remaining=len(self._connections),
        )

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the TCP receiver.

        Returns:
            Dictionary containing receiver status information
        """
        status = super().get_status()
        status.update({
            "queue_size": self._message_queue.qsize(),
            "queue_maxsize": self._message_queue.maxsize,
            "connections": len(self._connections),
            "max_connections": self.config.max_connections,
            "workers_active": len([t for t in self._worker_tasks if not t.done()]),
        })
        return status


class _TCPConnection:
    """Represents a single TCP connection.

    Handles message framing and buffering for a single client connection.
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        addr: tuple[str, int],
        connection_id: str,
        config: ReceiverConfig,
        logger: structlog.stdlib.BoundLogger,
        message_queue: asyncio.Queue,
    ) -> None:
        """Initialize the TCP connection.

        Args:
            reader: Stream reader for receiving data
            writer: Stream writer for sending data
            addr: Remote address (host, port)
            connection_id: Unique connection identifier
            config: Receiver configuration
            logger: Logger instance
            message_queue: Queue for received messages
        """
        self._reader = reader
        self._writer = writer
        self._addr = addr
        self._connection_id = connection_id
        self._config = config
        self._logger = logger.bind(
            connection_id=connection_id,
            remote_addr=addr[0],
        )
        self._message_queue = message_queue
        self._buffer = bytearray()
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def connection_id(self) -> str:
        """Get the connection ID."""
        return self._connection_id

    async def start(self) -> None:
        """Start processing data from this connection."""
        self._running = True
        self._task = asyncio.create_task(
            self._read_loop(),
            name=f"{self._connection_id}-reader",
        )
        self._logger.debug("Connection reader started")

    async def close(self) -> None:
        """Close the connection."""
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        try:
            self._writer.close()
            await asyncio.wait_for(self._writer.wait_closed(), timeout=1.0)
        except (asyncio.TimeoutError, Exception):
            pass

        self._logger.debug("Connection closed")

    async def _read_loop(self) -> None:
        """Read data loop for this connection."""
        self._logger.debug("Read loop started")

        try:
            while self._running:
                # Read data with timeout
                try:
                    data = await asyncio.wait_for(
                        self._reader.read(4096),
                        timeout=300.0,  # 5 minute timeout
                    )
                except asyncio.TimeoutError:
                    # Send keepalive and continue
                    continue

                if not data:
                    # Connection closed by client
                    break

                # Add to buffer
                self._buffer.extend(data)

                # Extract and process complete messages
                await self._process_messages()

        except asyncio.CancelledError:
            self._logger.debug("Read loop cancelled")
        except Exception as e:
            self._logger.error("Read loop error", error=str(e))
        finally:
            await self.close()

    async def _process_messages(self) -> None:
        """Process complete messages from the buffer."""
        while self._buffer:
            message, consumed = self._extract_message()

            if message is None:
                # No complete message yet
                break

            # Remove consumed bytes from buffer
            if consumed > 0:
                self._buffer = self._buffer[consumed:]

            # Create received message
            received_msg = ReceivedMessage(
                raw_data=message.encode("utf-8"),
                data=message,
                source=self._addr,
                received_at=datetime.now(),
                receiver_name=self._config.name,
            )

            # Put in queue (non-blocking, drop if full)
            try:
                self._message_queue.put_nowait(received_msg)
            except asyncio.QueueFull:
                self._logger.warning(
                    "Message queue full, dropping message",
                    queue_size=self._message_queue.qsize(),
                )

    def _extract_message(self) -> tuple[str | None, int]:
        """Extract a complete message from the buffer.

        Returns:
            Tuple of (message, bytes_consumed)

        Handles both octet-counting framing (RFC5425) and
        non-transparent framing (newline-delimited).
        """
        buffer_str = self._buffer.decode("utf-8", errors="replace")

        # Try octet-counting framing first (RFC5425)
        # Format: <length>SPACE<message>
        if len(self._buffer) > 0 and 48 <= self._buffer[0] <= 57:  # ASCII digit
            space_pos = buffer_str.find(" ")
            if space_pos > 0 and space_pos < 20:  # Reasonable length field size
                try:
                    length = int(buffer_str[:space_pos])
                    message_start = space_pos + 1
                    message_end = message_start + length

                    if len(self._buffer) >= message_end:
                        message = buffer_str[message_start:message_end]
                        return message, message_end
                except ValueError:
                    pass

        # Try newline-delimited framing (traditional syslog)
        newline_pos = buffer_str.find("\n")
        if newline_pos >= 0:
            message = buffer_str[:newline_pos].strip()
            return message, newline_pos + 1

        # No complete message yet
        return None, 0


class _TCPProtocol(asyncio.Protocol):
    """Protocol handler for TCP connections.

    Creates connection handlers for each incoming connection.
    """

    def __init__(
        self,
        message_queue: asyncio.Queue,
        config: ReceiverConfig,
        logger: structlog.stdlib.BoundLogger,
        on_open: callable,
        on_close: callable,
    ) -> None:
        """Initialize the TCP protocol.

        Args:
            message_queue: Queue to put received messages into
            config: Receiver configuration
            logger: Logger instance
            on_open: Callback when connection opens
            on_close: Callback when connection closes
        """
        self._queue = message_queue
        self._config = config
        self._logger = logger
        self._on_open = on_open
        self._on_close = on_close
        self._transport: asyncio.Transport | None = None
        self._peer_addr: tuple[str, int] | None = None

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Called when a connection is made."""
        self._transport = transport
        self._peer_addr = transport.get_extra_info("peername")

        # Generate connection ID
        connection_id = f"{self._peer_addr[0]}:{self._peer_addr[1]}-{id(transport)}"

        self._logger.debug(
            "TCP connection made",
            connection_id=connection_id,
            addr=self._peer_addr[0],
        )

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection is lost or closed."""
        if self._peer_addr:
            connection_id = f"{self._peer_addr[0]}:{self._peer_addr[1]}-{id(self._transport)}"
            asyncio.create_task(
                self._on_close(connection_id, self._peer_addr)
            )

        if exc:
            self._logger.error("TCP connection lost", error=str(exc))

    def data_received(self, data: bytes) -> None:
        """Called when data is received.

        Args:
            data: Received data bytes
        """
        # This is a simplified handler - in production, you would want
        # to use the _TCPConnection class for proper message framing
        try:
            message_text = data.decode("utf-8", errors="replace")

            message = ReceivedMessage(
                raw_data=data,
                data=message_text,
                source=self._peer_addr or ("unknown", 0),
                received_at=datetime.now(),
                receiver_name=self._config.name,
            )

            try:
                self._queue.put_nowait(message)
            except asyncio.QueueFull:
                self._logger.warning(
                    "Message queue full, dropping message",
                    addr=self._peer_addr[0] if self._peer_addr else "unknown",
                )

        except Exception as e:
            self._logger.error("Failed to process TCP data", error=str(e))

    def eof_received(self) -> bool:
        """Called when EOF is received."""
        return False  # Close the connection


class TLSTCPReceiver(TCPReceiver):
    """TCP receiver with TLS/SSL support.

    Provides encrypted syslog message reception over TCP.
    """

    def __init__(
        self,
        config: ReceiverConfig,
        certfile: str,
        keyfile: str,
        cafile: str | None = None,
        verify_client: bool = False,
    ) -> None:
        """Initialize the TLS TCP receiver.

        Args:
            config: Receiver configuration
            certfile: Path to server certificate file
            keyfile: Path to server private key file
            cafile: Path to CA certificate file (for client verification)
            verify_client: Whether to verify client certificates
        """
        super().__init__(config)
        self._certfile = certfile
        self._keyfile = keyfile
        self._cafile = cafile
        self._verify_client = verify_client
        self._ssl_context: asyncio.ssl.SSLContext | None = None

    async def _start_listener(self) -> None:
        """Start the TLS TCP socket listener."""
        import ssl

        # Create SSL context
        self._ssl_context = ssl.create_server_context(
            ssl.Purpose.CLIENT_AUTH,
            cafile=self._cafile,
        )

        self._ssl_context.load_cert_chain(
            certfile=self._certfile,
            keyfile=self._keyfile,
        )

        if self._verify_client:
            self._ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Create TCP server with SSL using start_server (Python 3.11+)
        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            """Handle incoming client connection with SSL."""
            addr = writer.get_extra_info("peername")
            connection_id = f"{addr[0]}:{addr[1]}-{id(writer)}"

            # Check connection limit
            async with self._connections_lock:
                if len(self._connections) >= self.config.max_connections:
                    self._logger.warning(
                        "Max connections reached, rejecting",
                        connection_id=connection_id,
                        addr=addr[0],
                        current=len(self._connections),
                    )
                    writer.close()
                    await writer.wait_closed()
                    return

                self._logger.debug(
                    "TLS Connection opened",
                    connection_id=connection_id,
                    addr=addr[0],
                    port=addr[1],
                    total=len(self._connections) + 1,
                )

            # Create connection handler
            conn = _TCPConnection(
                reader=reader,
                writer=writer,
                addr=addr,
                connection_id=connection_id,
                config=self.config,
                logger=self._logger,
                message_queue=self._message_queue,
            )

            async with self._connections_lock:
                self._connections[connection_id] = conn

            # Start connection reader
            await conn.start()

            await conn.close()

            async with self._connections_lock:
                if connection_id in self._connections:
                    del self._connections[connection_id]

            self._logger.debug(
                "TLS Connection closed",
                connection_id=connection_id,
                addr=addr[0],
                remaining=len(self._connections),
            )

        try:
            self._server = await asyncio.start_server(
                handle_client,
                host=self.config.host,
                port=self.config.port,
                reuse_address=True,
                reuse_port=True,
                ssl=self._ssl_context,
            )

            # Start serving
            await self._server.start_serving()

            self._logger.info(
                "TLS TCP receiver started",
                certfile=self._certfile,
                verify_client=self._verify_client,
            )

        except Exception as e:
            await self._close_socket()
            raise ReceiverStartError(f"Failed to start TLS TCP receiver: {e}")

    async def _close_socket(self) -> None:
        """Close the TLS TCP server and all connections."""
        await super()._close_socket()
        self._ssl_context = None
