"""
Asset Enricher for Syslog Server.

Enriches log entries with asset information based on device IP addresses.
Provides business context including system ownership, location, and responsibility.
"""

from __future__ import annotations

import asyncio
import ipaddress
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class AssetInfo(BaseModel):
    """Asset information model."""

    ip_address: str = Field(default="", description="Asset IP address")
    hostname: str | None = Field(default=None, description="Asset hostname")
    asset_name: str | None = Field(default=None, description="Asset name")
    asset_type: str | None = Field(default=None, description="Asset type (server/workstation/network/etc)")
    business_system: str | None = Field(default=None, description="Business system name")
    department: str | None = Field(default=None, description="Owning department")
    owner: str | None = Field(default=None, description="Asset owner")
    contact: str | None = Field(default=None, description="Contact information")
    location: str | None = Field(default=None, description="Physical location")
    site: str | None = Field(default=None, description="Site/campus")
    environment: str | None = Field(default=None, description="Environment (prod/staging/dev)")
    criticality: str | None = Field(default=None, description="Criticality level (high/medium/low)")
    tags: list[str] = Field(default_factory=list, description="Additional tags")
    custom_fields: dict[str, Any] = Field(default_factory=dict, description="Custom fields")


class AssetDatabase(ABC):
    """Abstract base class for asset database backends."""

    @abstractmethod
    async def get_asset(self, ip_address: str) -> AssetInfo | None:
        """Get asset information by IP address."""
        pass

    @abstractmethod
    async def get_asset_by_hostname(self, hostname: str) -> AssetInfo | None:
        """Get asset information by hostname."""
        pass

    @abstractmethod
    async def reload(self) -> None:
        """Reload asset database."""
        pass


@dataclass
class CacheEntry:
    """Cache entry for asset lookups."""

    asset: AssetInfo
    access_count: int = 0
    last_access: float = 0


class MemoryAssetDatabase(AssetDatabase):
    """In-memory asset database with LRU cache."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        cache_size: int = 10000,
    ):
        """Initialize the in-memory asset database."""
        self._assets: dict[str, AssetInfo] = {}
        self._hostname_index: dict[str, AssetInfo] = {}
        self._cache: dict[str, CacheEntry] = {}
        self._cache_size = cache_size

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str | Path) -> None:
        """Load assets from a YAML configuration file."""
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning("Asset config file not found", path=str(config_path))
            return

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
            assets = data.get("assets", [])

            for asset_data in assets:
                asset = AssetInfo(**asset_data)
                self._assets[asset.ip_address] = asset

                if asset.hostname:
                    self._hostname_index[asset.hostname] = asset

        logger.info("Loaded assets from file", count=len(self._assets))

    async def get_asset(self, ip_address: str) -> AssetInfo | None:
        """Get asset information by IP address."""
        return self._assets.get(ip_address)

    async def get_asset_by_hostname(self, hostname: str) -> AssetInfo | None:
        """Get asset information by hostname."""
        return self._hostname_index.get(hostname)

    async def reload(self) -> None:
        """Reload asset database (no-op for in-memory)."""
        pass

    def get_by_ip_range(self, ip_network: str) -> list[AssetInfo]:
        """Get all assets within an IP range."""
        network = ipaddress.ip_network(ip_network)
        return [
            asset
            for asset in self._assets.values()
            if asset.ip_address and asset.ip_address in network
        ]


class AssetEnricher:
    """Enriches log entries with asset information."""

    def __init__(
        self,
        database: AssetDatabase | None = None,
        enrich_device: bool = True,
        enrich_source: bool = True,
        enrich_destination: bool = True,
    ):
        """Initialize the asset enricher."""
        self._db = database or MemoryAssetDatabase()
        self._enrich_device = enrich_device
        self._enrich_source = enrich_source
        self._enrich_destination = enrich_destination

    async def enrich(self, log: dict[str, Any]) -> dict[str, Any]:
        """Enrich a single log entry with asset information."""
        if self._enrich_device and log.get("device_ip"):
            asset = await self._db.get_asset(log["device_ip"])
            if asset:
                log["asset_hostname"] = asset.hostname
                log["asset_name"] = asset.asset_name
                log["business_system"] = asset.business_system
                log["department"] = asset.department
                log["location"] = asset.location
                log["site"] = asset.site
                log["environment"] = asset.environment
                log["criticality"] = asset.criticality

        if self._enrich_source and log.get("src_ip"):
            asset = await self._db.get_asset(log["src_ip"])
            if asset:
                log["src_asset_hostname"] = asset.hostname
                log["src_business_system"] = asset.business_system
                log["src_location"] = asset.location
                log["src_site"] = asset.site

        if self._enrich_destination and log.get("dst_ip"):
            asset = await self._db.get_asset(log["dst_ip"])
            if asset:
                log["dst_asset_hostname"] = asset.hostname
                log["dst_business_system"] = asset.business_system
                log["dst_location"] = asset.location
                log["dst_site"] = asset.site

        return log

    async def enrich_batch(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enrich multiple log entries."""
        return [await self.enrich(log) for log in logs]

    def get_stats(self) -> dict[str, Any]:
        """Get enrichment statistics."""
        return {
            "total_assets": len(self._db._assets),
            "cached_assets": len(self._db._cache),
        }
