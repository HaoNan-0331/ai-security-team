"""
Enrichment Manager for Syslog Server.

Coordinates all enrichment modules and applies enrichment rules in sequence.
Provides batch processing optimization and error handling.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from syslog_server.config import settings
from syslog_server.enrichment.asset_enricher import AssetEnricher
from syslog_server.enrichment.geo_resolver import GeoResolver
from syslog_server.enrichment.mitre_mapper import MITREMapper
from syslog_server.enrichment.threat_tagger import ThreatTagger
from syslog_server.utils.logger import get_logger
from syslog_server.utils.metrics import Counter, Histogram, metrics

logger = get_logger(__name__)


# Enrichment metrics
enrichment_processed_total = Counter(
    "syslog_enrichment_processed_total",
    "Total number of logs processed by enrichment",
    ["status"],
    registry=metrics.registry,
)

enrichment_duration_seconds = Histogram(
    "syslog_enrichment_duration_seconds",
    "Enrichment processing duration in seconds",
    ["stage"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=metrics.registry,
)

enrichment_errors_total = Counter(
    "syslog_enrichment_errors_total",
    "Total number of enrichment errors",
    ["stage", "error_type"],
    registry=metrics.registry,
)


class EnrichmentStage(str, Enum):
    """Enrichment processing stages."""

    ASSET = "asset"
    GEO = "geo"
    THREAT = "threat"
    MITRE = "mitre"
    CUSTOM = "custom"


@dataclass
class EnrichmentResult:
    """Result of enrichment processing."""

    success: bool
    log: dict[str, Any]
    stages_applied: list[EnrichmentStage]
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0


@dataclass
class EnrichmentConfig:
    """Enrichment pipeline configuration."""

    # Enable/disable specific enrichers
    enable_asset: bool = True
    enable_geo: bool = True
    enable_threat: bool = True
    enable_mitre: bool = True

    # Configuration paths
    asset_config_path: str | None = None
    geoip_db_path: str | None = None
    threat_signatures_path: str | None = None
    mitre_config_path: str | None = None

    # Processing options
    parallel_stages: bool = True
    batch_size: int = 100
    continue_on_error: bool = True

    # Geo resolver options
    geo_enable_api_fallback: bool = True

    # Threat tagger options
    threat_risk_threshold: int = 30

    # MITRE mapper options
    mitre_confidence_threshold: float = 0.5

    # Asset enricher options
    asset_enrich_device: bool = True
    asset_enrich_source: bool = True
    asset_enrich_destination: bool = True

    @classmethod
    def from_settings(cls) -> "EnrichmentConfig":
        """Create configuration from application settings."""
        config_dir = settings.config_dir

        return cls(
            asset_config_path=str(config_dir / "assets.yaml"),
            geoip_db_path=str(settings.data_dir / "GeoLite2-City.mmdb"),
            threat_signatures_path=str(config_dir / "threat_signatures.yaml"),
            mitre_config_path=str(config_dir / "mitre_mappings.yaml"),
        )


class EnrichmentManager:
    """
    Main enrichment manager that coordinates all enrichment modules.

    Processes log entries through the enrichment pipeline in the configured order.
    """

    def __init__(
        self,
        config: EnrichmentConfig | None = None,
        asset_enricher: AssetEnricher | None = None,
        geo_resolver: GeoResolver | None = None,
        threat_tagger: ThreatTagger | None = None,
        mitre_mapper: MITREMapper | None = None,
    ):
        """
        Initialize the enrichment manager.

        Args:
            config: Enrichment configuration
            asset_enricher: Custom asset enricher instance
            geo_resolver: Custom geo resolver instance
            threat_tagger: Custom threat tagger instance
            mitre_mapper: Custom MITRE mapper instance
        """
        self.config = config or EnrichmentConfig.from_settings()

        # Enrichers (will be initialized during initialize())
        self.asset_enricher = asset_enricher
        self.geo_resolver = geo_resolver
        self.threat_tagger = threat_tagger
        self.mitre_mapper = mitre_mapper

        # Custom enrichers
        self._custom_enrichers: list[tuple[str, Callable]] = []

        # Statistics
        self._stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "stages": defaultdict(int),
            "errors": defaultdict(int),
            "total_duration_ms": 0,
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all enrichment modules."""
        logger.info("Initializing enrichment manager")

        # Initialize asset enricher
        if self.config.enable_asset and self.asset_enricher is None:
            self.asset_enricher = AssetEnricher(
                enrich_device=self.config.asset_enrich_device,
                enrich_source=self.config.asset_enrich_source,
                enrich_destination=self.config.asset_enrich_destination,
            )

        # Initialize geo resolver
        if self.config.enable_geo and self.geo_resolver is None:
            self.geo_resolver = GeoResolver.create_default(
                geoip2_db_path=self.config.geoip_db_path,
                enable_api_fallback=self.config.geo_enable_api_fallback,
            )

        # Initialize threat tagger
        if self.config.enable_threat and self.threat_tagger is None:
            self.threat_tagger = ThreatTagger(
                signatures_path=self.config.threat_signatures_path,
                risk_threshold=self.config.threat_risk_threshold,
            )

        # Initialize MITRE mapper
        if self.config.enable_mitre and self.mitre_mapper is None:
            self.mitre_mapper = MITREMapper(
                config_path=self.config.mitre_config_path,
                confidence_threshold=self.config.mitre_confidence_threshold,
            )

        # Initialize all enrichers
        init_tasks = []

        if self.asset_enricher:
            init_tasks.append(self.asset_enricher.initialize())
        if self.geo_resolver:
            init_tasks.append(self.geo_resolver.initialize())
        if self.threat_tagger:
            init_tasks.append(self.threat_tagger.initialize())
        if self.mitre_mapper:
            init_tasks.append(self.mitre_mapper.initialize())

        await asyncio.gather(*init_tasks, return_exceptions=True)

        self._initialized = True
        logger.info("Enrichment manager initialized")

    async def enrich(self, log: dict[str, Any]) -> EnrichmentResult:
        """
        Enrich a single log entry.

        Args:
            log: Log entry dictionary

        Returns:
            Enrichment result
        """
        if not self._initialized:
            await self.initialize()

        import time

        start_time = time.time()
        stages_applied = []
        errors = []

        try:
            # Define enrichment stages
            stages: list[tuple[EnrichmentStage, Callable | None]] = [
                (EnrichmentStage.ASSET, self.asset_enricher if self.config.enable_asset else None),
                (EnrichmentStage.GEO, self.geo_resolver if self.config.enable_geo else None),
                (EnrichmentStage.THREAT, self.threat_tagger if self.config.enable_threat else None),
                (EnrichmentStage.MITRE, self.mitre_mapper if self.config.enable_mitre else None),
            ]

            if self.config.parallel_stages:
                # Run independent stages in parallel
                await self._enrich_parallel(log, stages, stages_applied, errors)
            else:
                # Run stages sequentially
                await self._enrich_sequential(log, stages, stages_applied, errors)

            # Apply custom enrichers
            if self._custom_enrichers:
                for name, enricher_fn in self._custom_enrichers:
                    try:
                        await enricher_fn(log)
                        stages_applied.append(EnrichmentStage.CUSTOM)
                    except Exception as e:
                        error_msg = f"Custom enricher '{name}' failed: {str(e)}"
                        errors.append(error_msg)
                        self._stats["errors"][name] += 1
                        enrichment_errors_total.labels(stage="custom", error_type=type(e).__name__).inc()

                        if not self.config.continue_on_error:
                            raise

            duration_ms = (time.time() - start_time) * 1000

            # Update stats
            self._stats["processed"] += 1
            if not errors or self.config.continue_on_error:
                self._stats["successful"] += 1
            else:
                self._stats["failed"] += 1
            self._stats["total_duration_ms"] += duration_ms

            for stage in stages_applied:
                self._stats["stages"][stage.value] += 1

            enrichment_processed_total.labels(status="success" if not errors else "partial").inc()

            return EnrichmentResult(
                success=len(errors) == 0,
                log=log,
                stages_applied=stages_applied,
                errors=errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._stats["processed"] += 1
            self._stats["failed"] += 1
            self._stats["total_duration_ms"] += duration_ms

            error_msg = f"Enrichment failed: {str(e)}"
            errors.append(error_msg)
            self._stats["errors"]["general"] += 1

            enrichment_processed_total.labels(status="error").inc()
            enrichment_errors_total.labels(stage="general", error_type=type(e).__name__).inc()

            return EnrichmentResult(
                success=False,
                log=log,
                stages_applied=stages_applied,
                errors=errors,
                duration_ms=duration_ms,
            )

    async def _enrich_sequential(
        self,
        log: dict[str, Any],
        stages: list[tuple[EnrichmentStage, Callable | None]],
        stages_applied: list[EnrichmentStage],
        errors: list[str],
    ) -> None:
        """Run enrichment stages sequentially."""
        for stage_name, enricher in stages:
            if enricher is None:
                continue

            try:
                with metrics.timer(enrichment_duration_seconds, labels={"stage": stage_name.value}):
                    log = await enricher.enrich(log)
                stages_applied.append(stage_name)
            except Exception as e:
                error_msg = f"{stage_name.value} enrichment failed: {str(e)}"
                errors.append(error_msg)
                self._stats["errors"][stage_name.value] += 1
                enrichment_errors_total.labels(stage=stage_name.value, error_type=type(e).__name__).inc()

                if not self.config.continue_on_error:
                    raise

    async def _enrich_parallel(
        self,
        log: dict[str, Any],
        stages: list[tuple[EnrichmentStage, Callable | None]],
        stages_applied: list[EnrichmentStage],
        errors: list[str],
    ) -> None:
        """Run independent enrichment stages in parallel."""
        # Group stages by dependency
        # Asset and Geo are independent, Threat and MITRE depend on previous results
        independent_stages = []
        dependent_stages = []

        for stage_name, enricher in stages:
            if enricher is None:
                continue
            if stage_name in [EnrichmentStage.ASSET, EnrichmentStage.GEO]:
                independent_stages.append((stage_name, enricher))
            else:
                dependent_stages.append((stage_name, enricher))

        # Run independent stages in parallel
        if independent_stages:
            results = await asyncio.gather(
                *[
                    self._safe_enrich(stage, enricher, log)
                    for stage, enricher in independent_stages
                ],
                return_exceptions=False,
            )

            for stage_name, result_log, error in results:
                if error:
                    errors.append(error)
                    self._stats["errors"][stage_name.value] += 1
                    if not self.config.continue_on_error:
                        raise Exception(error)
                else:
                    log.update(result_log)
                    stages_applied.append(stage_name)

        # Run dependent stages in parallel
        if dependent_stages:
            results = await asyncio.gather(
                *[
                    self._safe_enrich(stage, enricher, log)
                    for stage, enricher in dependent_stages
                ],
                return_exceptions=False,
            )

            for stage_name, result_log, error in results:
                if error:
                    errors.append(error)
                    self._stats["errors"][stage_name.value] += 1
                    if not self.config.continue_on_error:
                        raise Exception(error)
                else:
                    log.update(result_log)
                    stages_applied.append(stage_name)

    async def _safe_enrich(
        self,
        stage: EnrichmentStage,
        enricher: Callable,
        log: dict[str, Any],
    ) -> tuple[EnrichmentStage, dict[str, Any], str | None]:
        """Safely execute enrichment with error handling."""
        try:
            with metrics.timer(enrichment_duration_seconds, labels={"stage": stage.value}):
                result = await enricher.enrich(log)
            return stage, result, None
        except Exception as e:
            return stage, log, f"{stage.value} enrichment failed: {str(e)}"

    async def enrich_batch(self, logs: list[dict[str, Any]]) -> list[EnrichmentResult]:
        """
        Enrich multiple log entries.

        Args:
            logs: List of log entries

        Returns:
            List of enrichment results
        """
        if not self._initialized:
            await self.initialize()

        results = []

        for i in range(0, len(logs), self.config.batch_size):
            batch = logs[i : i + self.config.batch_size]

            # Process batch
            batch_results = await asyncio.gather(*[self.enrich(log) for log in batch])
            results.extend(batch_results)

        return results

    def add_custom_enricher(self, name: str, enricher_fn: Callable) -> None:
        """
        Add a custom enrichment function.

        Args:
            name: Enricher name
            enricher_fn: Async function that takes a log dict and returns it enriched
        """
        self._custom_enrichers.append((name, enricher_fn))
        logger.info("Custom enricher added", name=name)

    def remove_custom_enricher(self, name: str) -> bool:
        """
        Remove a custom enrichment function.

        Args:
            name: Enricher name

        Returns:
            True if removed, False if not found
        """
        for i, (n, _) in enumerate(self._custom_enrichers):
            if n == name:
                self._custom_enrichers.pop(i)
                logger.info("Custom enricher removed", name=name)
                return True
        return False

    async def get_stats(self) -> dict[str, Any]:
        """Get enrichment statistics."""
        stats = {
            "initialized": self._initialized,
            "config": {
                "enable_asset": self.config.enable_asset,
                "enable_geo": self.config.enable_geo,
                "enable_threat": self.config.enable_threat,
                "enable_mitre": self.config.enable_mitre,
                "parallel_stages": self.config.parallel_stages,
                "batch_size": self.config.batch_size,
            },
            "stats": {
                "processed": self._stats["processed"],
                "successful": self._stats["successful"],
                "failed": self._stats["failed"],
                "stages": dict(self._stats["stages"]),
                "errors": dict(self._stats["errors"]),
                "total_duration_ms": self._stats["total_duration_ms"],
                "avg_duration_ms": (
                    self._stats["total_duration_ms"] / self._stats["processed"]
                    if self._stats["processed"] > 0
                    else 0
                ),
            },
            "custom_enrichers": [name for name, _ in self._custom_enrichers],
        }

        # Get enricher-specific stats
        if self.asset_enricher:
            stats["asset_enricher"] = await self.asset_enricher.get_stats()
        if self.geo_resolver:
            stats["geo_resolver"] = await self.geo_resolver.get_stats()
        if self.threat_tagger:
            stats["threat_tagger"] = await self.threat_tagger.get_stats()
        if self.mitre_mapper:
            stats["mitre_mapper"] = await self.mitre_mapper.get_stats()

        return stats

    async def shutdown(self) -> None:
        """Shutdown the enrichment manager and cleanup resources."""
        logger.info("Shutting down enrichment manager")

        shutdown_tasks = []

        if self.asset_enricher:
            shutdown_tasks.append(self.asset_enricher.shutdown())
        if self.geo_resolver:
            shutdown_tasks.append(self.geo_resolver.shutdown())
        if self.threat_tagger:
            shutdown_tasks.append(self.threat_tagger.shutdown())

        await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        self._initialized = False
        logger.info("Enrichment manager shutdown")

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "stages": defaultdict(int),
            "errors": defaultdict(int),
            "total_duration_ms": 0,
        }

        if self.threat_tagger:
            self.threat_tagger.reset_stats()


# Singleton instance
enrichment_manager = EnrichmentManager()
