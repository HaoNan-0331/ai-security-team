"""
Syslog Server - Main Entry Point

Enterprise log collection and analysis system.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI

from syslog_server.api.app import create_api_app
from syslog_server.api.routes.logs import set_storage_manager
from syslog_server.config import settings
from syslog_server.storage.manager import StorageManager
from syslog_server.utils.logger import configure_logging
from syslog_server.receivers.manager import ReceiverManager

# Configure logging
configure_logging()
logger = structlog.get_logger(__name__)


# Global managers
storage_manager: StorageManager | None = None
receiver_manager: ReceiverManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Syslog Server", version="1.0.0")

    global storage_manager

    try:
        # Initialize storage manager
        storage_manager = StorageManager(settings.database_url, settings.redis_url)
        await storage_manager.initialize()
        logger.info("Storage manager initialized")

        # Set storage manager for API routes
        set_storage_manager(storage_manager)

        # Initialize receiver manager
        receiver_manager = ReceiverManager(storage_manager)
        await receiver_manager.load_config()
        await receiver_manager.start()
        logger.info("Receiver manager started")

        yield

    except Exception as e:
        logger.error("Failed to initialize server", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Syslog Server")

        if receiver_manager:
            await receiver_manager.stop()
            logger.info("Receiver manager stopped")

        if storage_manager:
            await storage_manager.close()
            logger.info("Storage manager closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = create_api_app(lifespan=lifespan)
    return app


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Log startup
    logger.info(
        "Syslog Server starting",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level,
    )

    # Run with uvicorn
    uvicorn.run(
        "syslog_server.main:create_app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.workers > 1 else None,
        log_level=settings.log_level.lower(),
        reload=settings.workers == 1,  # Enable reload in development
        factory=True,
    )


if __name__ == "__main__":
    main()
