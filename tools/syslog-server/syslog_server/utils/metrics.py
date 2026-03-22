"""
Prometheus metrics for Syslog Server.

Provides metrics collection and exposition for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, generate_latest

from syslog_server.config import settings


# Create a custom registry
registry = CollectorRegistry()


# ========== Receivers Metrics ==========

# Messages received total
messages_received_total = Counter(
    "syslog_messages_received_total",
    "Total number of syslog messages received",
    ["receiver", "protocol", "format"],
    registry=registry,
)

# Messages parsed total
messages_parsed_total = Counter(
    "syslog_messages_parsed_total",
    "Total number of syslog messages parsed",
    ["parser", "status"],
    registry=registry,
)

# Messages stored total
messages_stored_total = Counter(
    "syslog_messages_stored_total",
    "Total number of syslog messages stored",
    ["backend", "status"],
    registry=registry,
)

# Parse errors total
parse_errors_total = Counter(
    "syslog_parse_errors_total",
    "Total number of parse errors",
    ["parser", "error_type"],
    registry=registry,
)


# ========== Storage Metrics ==========

# Queue size
queue_size = Gauge(
    "syslog_queue_size",
    "Current size of the message processing queue",
    registry=registry,
)

# Storage backend status
storage_status = Gauge(
    "syslog_storage_status",
    "Storage backend status (1=connected, 0=disconnected)",
    ["backend"],
    registry=registry,
)

# Storage usage
storage_usage_bytes = Gauge(
    "syslog_storage_usage_bytes",
    "Storage usage in bytes",
    registry=registry,
)

# Logs total in database
logs_total = Gauge(
    "syslog_logs_total",
    "Total number of logs in the database",
    registry=registry,
)


# ========== API Metrics ==========

# API requests total
api_requests_total = Counter(
    "syslog_api_requests_total",
    "Total number of API requests",
    ["endpoint", "method", "status"],
    registry=registry,
)

# API request duration
api_request_duration_seconds = Histogram(
    "syslog_api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
    registry=registry,
)

# Active connections
api_connections_active = Gauge(
    "syslog_api_connections_active",
    "Number of active API connections",
    registry=registry,
)


# ========== System Metrics ==========

# CPU usage percent
cpu_usage_percent = Gauge(
    "syslog_cpu_usage_percent",
    "CPU usage percentage",
    registry=registry,
)

# Memory usage bytes
memory_usage_bytes = Gauge(
    "syslog_memory_usage_bytes",
    "Memory usage in bytes",
    registry=registry,
)


# ========== Utilities ==========

def get_metrics() -> bytes:
    """Get all metrics in Prometheus text format."""
    return generate_latest(registry)


class MetricsContext:
    """Context manager for timing operations."""

    def __init__(self, histogram: Histogram, labels: dict | None = None):
        self.histogram = histogram
        self.labels = labels or {}

    def __enter__(self):
        self.timer = self.histogram.time(**self.labels)
        self.timer.__enter__()
        return self

    def __exit__(self, *args):
        self.timer.__exit__(*args)


# Singleton instance for easy import
class _Metrics:
    """Metrics accessor class."""

    @property
    def messages_received(self):
        return messages_received_total

    @property
    def messages_parsed(self):
        return messages_parsed_total

    @property
    def messages_stored(self):
        return messages_stored_total

    @property
    def parse_errors(self):
        return parse_errors_total

    @property
    def api_requests(self):
        return api_requests_total

    @property
    def api_duration(self):
        return api_request_duration_seconds

    @property
    def queue_size(self):
        return queue_size

    @property
    def storage_status(self):
        return storage_status

    @property
    def logs_total(self):
        return logs_total

    def timer(self, histogram: Histogram, labels: dict | None = None):
        """Create a timing context."""
        return MetricsContext(histogram, labels)

    def export(self) -> bytes:
        """Export metrics in Prometheus format."""
        return get_metrics()


metrics = _Metrics()
