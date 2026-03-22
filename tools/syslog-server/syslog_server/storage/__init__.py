"""Storage layer for Syslog Server."""

from .manager import StorageManager
from .models import LogEntry, LogQuery, PaginatedResult

__all__ = [
    "StorageManager",
    "LogEntry",
    "LogQuery",
    "PaginatedResult",
    "get_storage_manager",
    "set_storage_manager",
]

# Global storage manager instance
_storage_manager: StorageManager | None = None


def get_storage_manager() -> StorageManager | None:
    """Get the global storage manager instance."""
    return _storage_manager


def set_storage_manager(manager: StorageManager) -> None:
    """Set the global storage manager instance."""
    global _storage_manager
    _storage_manager = manager
