"""
Geo Resolver for Syslog Server.

Resolves geographic location information from IP addresses.
Supports multiple backends including GeoIP2 databases and online APIs.
"""

import asyncio
import ipaddress
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from syslog_server.utils.logger import get_logger

logger = get_logger(__name__)


class Continent(str, Enum):
    """ISO 3166-1 alpha-2 continent codes."""

    AFRICA = "AF"
    ASIA = "AS"
    EUROPE = "EU"
    NORTH_AMERICA = "NA"
    OCEANIA = "OC"
    SOUTH_AMERICA = "SA"
    ANTARCTICA = "AN"


@dataclass
class GeoLocation:
    """Geographic location information."""

    country_code: str | None = None
    country_name: str | None = None
    continent_code: Continent | None = None
    region_code: str | None = None
    region_name: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    is_eu: bool | None = None
    is_anonymous_proxy: bool = False
    is_satellite_provider: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "continent_code": self.continent_code.value if self.continent_code else None,
            "region_code": self.region_code,
            "region_name": self.region_name,
            "city": self.city,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "is_eu": self.is_eu,
            "is_anonymous_proxy": self.is_anonymous_proxy,
            "is_satellite_provider": self.is_satellite_provider,
        }


class GeoBackend(ABC):
    """Abstract base class for geo-location backends."""

    @abstractmethod
    async def resolve(self, ip_address: str) -> GeoLocation | None:
        """Resolve geographic location for an IP address."""
        pass

    @abstractmethod
    async def resolve_batch(self, ip_addresses: list[str]) -> list[GeoLocation | None]:
        """Resolve multiple IP addresses."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available."""
        pass


class GeoIP2Backend(GeoBackend):
    """
    GeoIP2 database backend.

    Uses MaxMind GeoIP2 database for IP geolocation.
    Requires geoip2 package to be installed.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        cache_enabled: bool = True,
        cache_size: int = 10000,
    ):
        """
        Initialize GeoIP2 backend.

        Args:
            db_path: Path to GeoIP2 database file (.mmdb)
            cache_enabled: Enable in-memory caching
            cache_size: Maximum cache size
        """
        self.db_path = Path(db_path) if db_path else None
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size

        self._reader: Any = None
        self._cache: dict[str, GeoLocation] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        self._available = False

    async def initialize(self) -> None:
        """Initialize the GeoIP2 reader."""
        try:
            import geoip2.database
        except ImportError:
            logger.warning("geoip2 package not installed, GeoIP2 backend unavailable")
            return

        # Try default paths if not specified
        if not self.db_path:
            default_paths = [
                "/usr/share/GeoIP/GeoLite2-City.mmdb",
                "/var/lib/GeoIP/GeoLite2-City.mmdb",
                "/app/data/GeoLite2-City.mmdb",
            ]
            for path in default_paths:
                if Path(path).exists():
                    self.db_path = Path(path)
                    break

        if not self.db_path or not self.db_path.exists():
            logger.warning("GeoIP2 database not found", path=str(self.db_path))
            return

        try:
            self._reader = geoip2.database.Reader(str(self.db_path))
            self._available = True
            logger.info("GeoIP2 backend initialized", db_path=str(self.db_path))
        except Exception as e:
            logger.error("Failed to initialize GeoIP2 reader", error=str(e))

    def is_available(self) -> bool:
        """Check if the backend is available."""
        return self._available

    async def resolve(self, ip_address: str) -> GeoLocation | None:
        """Resolve geographic location for an IP address."""
        if not self._available:
            return None

        # Check cache
        if self.cache_enabled and ip_address in self._cache:
            self._cache_hits += 1
            return self._cache[ip_address]

        self._cache_misses += 1

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._do_resolve, ip_address)

            if response and self.cache_enabled:
                self._add_to_cache(ip_address, response)

            return response
        except Exception as e:
            logger.debug("Failed to resolve IP", ip=ip_address, error=str(e))
            return None

    def _do_resolve(self, ip_address: str) -> GeoLocation | None:
        """Synchronous resolve operation."""
        try:
            response = self._reader.city(ip_address)

            location = GeoLocation(
                country_code=response.country.iso_code,
                country_name=response.country.name,
                continent_code=self._parse_continent(response.continent.code),
                region_code=response.subdivisions.most_specific.iso_code if response.subdivisions.most_specific else None,
                region_name=response.subdivisions.most_specific.name if response.subdivisions.most_specific else None,
                city=response.city.name,
                postal_code=response.postal.code,
                latitude=response.location.latitude if response.location else None,
                longitude=response.location.longitude if response.location else None,
                timezone=response.location.time_zone if response.location else None,
                is_eu=response.country.is_in_european_union,
            )

            # Check for anonymous/proxy
            if hasattr(response, "traits"):
                location.is_anonymous_proxy = response.traits.is_anonymous_proxy
                location.is_satellite_provider = response.traits.is_satellite_provider

            return location
        except Exception:
            return None

    def _parse_continent(self, code: str | None) -> Continent | None:
        """Parse continent code."""
        if not code:
            return None
        try:
            return Continent(code.upper())
        except ValueError:
            return None

    async def resolve_batch(self, ip_addresses: list[str]) -> list[GeoLocation | None]:
        """Resolve multiple IP addresses."""
        tasks = [self.resolve(ip) for ip in ip_addresses]
        return await asyncio.gather(*tasks)

    def _add_to_cache(self, ip: str, location: GeoLocation) -> None:
        """Add entry to cache with LRU eviction."""
        if not self.cache_enabled:
            return

        if len(self._cache) >= self.cache_size:
            # Simple FIFO eviction
            self._cache.pop(next(iter(self._cache)))

        self._cache[ip] = location

    @property
    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0

        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
        }

    async def shutdown(self) -> None:
        """Shutdown the backend."""
        if self._reader:
            self._reader.close()
            self._available = False


class APIGeoBackend(GeoBackend):
    """
    Online API-based geo-location backend.

    Supports multiple geo-location APIs as fallback.
    """

    def __init__(
        self,
        api_url: str = "https://ip-api.com/json/{ip}",
        timeout: float = 1.0,
        batch_size: int = 50,
        rate_limit: int = 100,
    ):
        """
        Initialize API backend.

        Args:
            api_url: API URL template (use {ip} as placeholder)
            timeout: Request timeout in seconds
            batch_size: Maximum concurrent requests
            rate_limit: Requests per second limit
        """
        self.api_url = api_url
        self.timeout = timeout
        self.batch_size = batch_size
        self.rate_limit = rate_limit

        self._semaphore = asyncio.Semaphore(batch_size)
        self._request_times: list[float] = []
        self._available = True

    async def _check_rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        # Remove requests older than 1 second
        self._request_times = [t for t in self._request_times if now - t < 1.0]

        if len(self._request_times) >= self.rate_limit:
            # Wait for oldest request to expire
            sleep_time = 1.0 - (now - self._request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self._request_times.append(now)

    def is_available(self) -> bool:
        """Check if the backend is available."""
        return self._available

    async def resolve(self, ip_address: str) -> GeoLocation | None:
        """Resolve geographic location using API."""
        if not self._available:
            return None

        async with self._semaphore:
            await self._check_rate_limit()

            try:
                import httpx

                url = self.api_url.replace("{ip}", ip_address)

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()

                    return self._parse_response(data)
            except Exception as e:
                logger.debug("API geo resolve failed", ip=ip_address, error=str(e))
                return None

    def _parse_response(self, data: dict[str, Any]) -> GeoLocation | None:
        """Parse API response."""
        # Support ip-api.com format
        if data.get("status") == "fail":
            return None

        return GeoLocation(
            country_code=data.get("countryCode"),
            country_name=data.get("country"),
            region_code=data.get("region"),
            region_name=data.get("regionName"),
            city=data.get("city"),
            postal_code=data.get("zip"),
            latitude=data.get("lat"),
            longitude=data.get("lon"),
            timezone=data.get("timezone"),
            is_anonymous_proxy=data.get("proxy", False),
            is_satellite_provider=data.get("satellite", False),
        )

    async def resolve_batch(self, ip_addresses: list[str]) -> list[GeoLocation | None]:
        """Resolve multiple IP addresses."""
        tasks = [self.resolve(ip) for ip in ip_addresses]
        return await asyncio.gather(*tasks)


class GeoResolver:
    """
    Geographic location resolver.

    Resolves geographic information from IP addresses with multiple backend support.
    """

    def __init__(
        self,
        backends: list[GeoBackend] | None = None,
        enrich_device: bool = False,
        enrich_source: bool = True,
        enrich_destination: bool = True,
        field_mapping: dict[str, str] | None = None,
    ):
        """
        Initialize the geo resolver.

        Args:
            backends: List of geo-location backends (tried in order)
            enrich_device: Enrich device IP
            enrich_source: Enrich source IP
            enrich_destination: Enrich destination IP
            field_mapping: Custom field mapping
        """
        self.backends = backends or []
        self.enrich_device = enrich_device
        self.enrich_source = enrich_source
        self.enrich_destination = enrich_destination

        self.field_mapping = field_mapping or {
            "country_code": "src_geo_country_code",
            "country_name": "src_geo_country",
            "city": "src_geo_city",
            "region": "src_geo_region",
            "latitude": "src_geo_lat",
            "longitude": "src_geo_lon",
            "timezone": "src_geo_timezone",
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the resolver and backends."""
        for backend in self.backends:
            if hasattr(backend, "initialize"):
                await backend.initialize()

        self._initialized = True
        available = [b for b in self.backends if b.is_available()]
        logger.info(
            "Geo resolver initialized",
            total_backends=len(self.backends),
            available_backends=len(available),
        )

    async def resolve(self, ip_address: str) -> GeoLocation | None:
        """
        Resolve geographic location for an IP address.

        Tries each backend in order until one returns a result.
        """
        if not self._initialized:
            await self.initialize()

        for backend in self.backends:
            if not backend.is_available():
                continue

            try:
                result = await backend.resolve(ip_address)
                if result:
                    return result
            except Exception as e:
                logger.debug("Backend resolve failed", backend=type(backend).__name__, error=str(e))

        return None

    async def enrich(self, log: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich a log entry with geographic information.

        Args:
            log: Log entry dictionary

        Returns:
            Enriched log entry
        """
        if not self._initialized:
            await self.initialize()

        # Enrich source IP
        if self.enrich_source and log.get("src_ip"):
            src_geo = await self.resolve(log["src_ip"])
            if src_geo:
                log = self._apply_geo_info(log, src_geo, "src")

        # Enrich destination IP
        if self.enrich_destination and log.get("dst_ip"):
            dst_geo = await self.resolve(log["dst_ip"])
            if dst_geo:
                log = self._apply_geo_info(log, dst_geo, "dst")

        # Enrich device IP
        if self.enrich_device and log.get("device_ip"):
            device_geo = await self.resolve(log["device_ip"])
            if device_geo:
                log = self._apply_geo_info(log, device_geo, "device")

        return log

    async def enrich_batch(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Enrich multiple log entries.

        Args:
            logs: List of log entries

        Returns:
            List of enriched log entries
        """
        if not self._initialized:
            await self.initialize()

        return await asyncio.gather(*[self.enrich(log) for log in logs])

    def _apply_geo_info(self, log: dict[str, Any], geo: GeoLocation, prefix: str) -> dict[str, Any]:
        """Apply geographic information to log entry."""
        prefix_map = {
            "src": "src_geo",
            "dst": "dst_geo",
            "device": "device_geo",
        }

        base_prefix = prefix_map.get(prefix, f"{prefix}_geo")

        # Apply fields
        geo_dict = geo.to_dict()
        for key, value in geo_dict.items():
            if value is not None:
                field_name = self.field_mapping.get(key, f"{base_prefix}_{key}")
                log[field_name] = value

        # Legacy field support (backward compatibility)
        if geo.country_name:
            log[f"{base_prefix}_country"] = geo.country_name
        if geo.city:
            log[f"{base_prefix}_city"] = geo.city

        return log

    async def get_stats(self) -> dict[str, Any]:
        """Get resolver statistics."""
        stats = {
            "initialized": self._initialized,
            "enrich_device": self.enrich_device,
            "enrich_source": self.enrich_source,
            "enrich_destination": self.enrich_destination,
            "backends": [],
        }

        for backend in self.backends:
            backend_stats = {"type": type(backend).__name__, "available": backend.is_available()}

            if hasattr(backend, "cache_stats"):
                backend_stats["cache"] = backend.cache_stats

            stats["backends"].append(backend_stats)

        return stats

    async def shutdown(self) -> None:
        """Shutdown the resolver and backends."""
        for backend in self.backends:
            if hasattr(backend, "shutdown"):
                await backend.shutdown()
        logger.info("Geo resolver shutdown")

    @classmethod
    def create_default(
        cls,
        geoip2_db_path: str | Path | None = None,
        enable_api_fallback: bool = True,
    ) -> "GeoResolver":
        """
        Create a geo resolver with default backends.

        Args:
            geoip2_db_path: Path to GeoIP2 database
            enable_api_fallback: Enable API fallback

        Returns:
            Configured GeoResolver instance
        """
        backends = []

        # Add GeoIP2 backend
        geoip2 = GeoIP2Backend(db_path=geoip2_db_path)
        backends.append(geoip2)

        # Add API fallback
        if enable_api_fallback:
            api_backend = APIGeoBackend()
            backends.append(api_backend)

        return cls(backends=backends)
