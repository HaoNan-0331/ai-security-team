"""
Application settings management.

Loads configuration from environment variables and provides type-safe access.
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========== Server Configuration ==========
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    log_level: str = Field(default="INFO", description="Log level")

    # ========== Database Configuration ==========
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="syslog", description="Database name")
    db_user: str = Field(default="syslog_user", description="Database user")
    db_password: str = Field(default="", description="Database password")
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=40, description="Database max overflow")

    @property
    def database_url(self) -> str:
        """Get the database connection URL (async)."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # ========== Redis Configuration ==========
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_max_connections: int = Field(default=50, description="Redis max connections")

    @property
    def redis_url(self) -> str:
        """Get the Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ========== Configuration Paths ==========
    receiver_config_path: str = Field(
        default="/app/config/receivers.yaml",
        description="Path to receiver configuration file"
    )
    parser_config_path: str = Field(
        default="/app/config/parsers.yaml",
        description="Path to parser configuration file"
    )

    # ========== Enrichment Configuration ==========
    enrichment_asset_config_path: str = Field(
        default="/app/config/assets.yaml",
        description="Path to asset configuration file"
    )
    enrichment_threat_signatures_path: str = Field(
        default="/app/config/threat_signatures.yaml",
        description="Path to threat signatures file"
    )
    enrichment_mitre_config_path: str = Field(
        default="/app/config/mitre_mappings.yaml",
        description="Path to MITRE mappings file"
    )
    enrichment_ip_reputation_path: str = Field(
        default="/app/config/ip_reputation.yaml",
        description="Path to IP reputation file"
    )
    enrichment_geoip_db_path: str = Field(
        default="/app/data/GeoLite2-City.mmdb",
        description="Path to GeoIP2 database file"
    )

    # Enrichment feature flags
    enrichment_enable_asset: bool = Field(default=True, description="Enable asset enrichment")
    enrichment_enable_geo: bool = Field(default=True, description="Enable geo-location enrichment")
    enrichment_enable_threat: bool = Field(default=True, description="Enable threat detection")
    enrichment_enable_mitre: bool = Field(default=True, description="Enable MITRE ATT&CK mapping")
    enrichment_parallel_stages: bool = Field(default=True, description="Run enrichment stages in parallel")
    enrichment_batch_size: int = Field(default=100, description="Batch size for enrichment processing")
    enrichment_continue_on_error: bool = Field(default=True, description="Continue enrichment on error")

    # Threat detection settings
    enrichment_threat_risk_threshold: int = Field(
        default=30,
        description="Minimum risk score for threat tagging"
    )

    # MITRE mapping settings
    enrichment_mitre_confidence_threshold: float = Field(
        default=0.5,
        description="Minimum confidence for MITRE mapping"
    )

    # Asset enrichment settings
    enrichment_asset_enrich_device: bool = Field(default=True, description="Enrich device IP")
    enrichment_asset_enrich_source: bool = Field(default=True, description="Enrich source IP")
    enrichment_asset_enrich_destination: bool = Field(default=True, description="Enrich destination IP")

    # ========== Storage Configuration ==========
    hot_data_days: int = Field(default=30, description="Hot data retention days")
    warm_data_days: int = Field(default=60, description="Warm data retention days")
    cold_data_days: int = Field(default=275, description="Cold data retention days")

    @property
    def total_retention_days(self) -> int:
        """Get total retention days."""
        return self.hot_data_days + self.warm_data_days + self.cold_data_days

    # ========== API Configuration ==========
    api_max_page_size: int = Field(default=1000, description="Max page size for API")
    api_default_page_size: int = Field(default=100, description="Default page size for API")
    api_secret_key: str = Field(default="change-me", description="API secret key")
    api_token_header: str = Field(default="X-API-Token", description="API token header name")

    # ========== Security ==========
    allowed_hosts: List[str] = Field(default=["*"], description="Allowed hosts for CORS")
    enable_cors: bool = Field(default=True, description="Enable CORS")

    # ========== Paths ==========
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return get_project_root()

    @property
    def config_dir(self) -> Path:
        """Get configuration directory."""
        config_path = Path(self.receiver_config_path).parent
        return config_path if config_path.exists() else self.project_root / "config"

    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        return Path(os.getenv("SYSLOG_DATA_DIR", "/app/data"))

    @property
    def log_dir(self) -> Path:
        """Get log directory."""
        return Path(os.getenv("SYSLOG_LOG_DIR", "/app/logs"))


# Global settings instance
settings = Settings()
