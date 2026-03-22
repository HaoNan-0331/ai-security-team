"""
Data enrichment module for Syslog Server.

Provides enrichment capabilities for log entries including:
- Asset association
- Geographic location resolution
- Threat detection and tagging
- MITRE ATT&CK mapping
"""

__all__ = [
    "EnrichmentManager",
    "enrichment_manager",
    "AssetEnricher",
    "AssetInfo",
    "MemoryAssetDatabase",
    "GeoResolver",
    "ThreatTagger",
    "MITREMapper",
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "AssetEnricher":
        from syslog_server.enrichment.asset_enricher import AssetEnricher
        return AssetEnricher
    if name == "AssetInfo":
        from syslog_server.enrichment.asset_enricher import AssetInfo
        return AssetInfo
    if name == "MemoryAssetDatabase":
        from syslog_server.enrichment.asset_enricher import MemoryAssetDatabase
        return MemoryAssetDatabase
    if name == "GeoResolver":
        from syslog_server.enrichment.geo_resolver import GeoResolver
        return GeoResolver
    if name == "ThreatTagger":
        from syslog_server.enrichment.threat_tagger import ThreatTagger
        return ThreatTagger
    if name == "MITREMapper":
        from syslog_server.enrichment.mitre_mapper import MITREMapper
        return MITREMapper
    if name == "EnrichmentManager":
        from syslog_server.enrichment.manager import EnrichmentManager
        return EnrichmentManager
    if name == "enrichment_manager":
        from syslog_server.enrichment.manager import enrichment_manager
        return enrichment_manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
