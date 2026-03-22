"""
Configuration loader for receiver configurations.

Provides utilities for loading and validating receiver configurations
from YAML files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import structlog
import yaml
from pydantic import BaseModel, Field, field_validator
from syslog_server.config import settings

logger = structlog.get_logger(__name__)


class ReceiverConfigModel(BaseModel):
    """Receiver configuration model with validation.

    Attributes:
        name: Unique name for this receiver
        protocol: Protocol type (udp/tcp/tls)
        host: Host address to bind to
        port: Port to listen on
        format: Log format (rfc5424/rfc3164/cef/json)
        enabled: Whether this receiver is enabled
        workers: Number of worker tasks for processing
        buffer_size: Buffer size for socket operations (bytes)
        max_connections: Maximum concurrent connections (TCP/TLS only)
        batch_size: Batch size for UDP receiver
        batch_timeout: Batch timeout for UDP receiver (seconds)
        tls_certfile: Path to TLS certificate file (TLS only)
        tls_keyfile: Path to TLS key file (TLS only)
        tls_cafile: Path to TLS CA file (TLS only)
        tls_verify_client: Whether to verify client certificates (TLS only)
        parser_options: Additional options for the parser
        description: Human-readable description
    """

    name: str = Field(..., min_length=1, description="Unique name for this receiver")
    protocol: str = Field(..., pattern="^(udp|tcp|tls)$", description="Protocol type")
    host: str = Field(default="0.0.0.0", description="Bind address")
    port: int = Field(..., ge=1, le=65535, description="Bind port")
    format: str = Field(
        default="rfc5424",
        pattern="^(rfc5424|rfc3164|cef|json|plain)$",
        description="Log format",
    )
    enabled: bool = Field(default=True, description="Enable/disable receiver")
    workers: int = Field(default=4, ge=1, le=100, description="Number of workers")
    buffer_size: int = Field(default=1048576, ge=4096, description="Buffer size in bytes")
    max_connections: int = Field(default=1000, ge=1, description="Max concurrent connections")
    batch_size: int = Field(default=100, ge=1, description="Batch size for UDP")
    batch_timeout: float = Field(default=0.1, ge=0.001, le=10.0, description="Batch timeout (seconds)")
    tls_certfile: str | None = Field(default=None, description="TLS certificate file path")
    tls_keyfile: str | None = Field(default=None, description="TLS key file path")
    tls_cafile: str | None = Field(default=None, description="TLS CA file path")
    tls_verify_client: bool = Field(default=False, description="Verify client certificates")
    parser_options: dict[str, Any] = Field(
        default_factory=dict, description="Parser options"
    )
    description: str = Field(default="", description="Receiver description")

    @field_validator("port")
    @classmethod
    def check_port_permissions(cls, v: int, info) -> int:
        """Warn if port requires special permissions."""
        if v < 1024:
            logger.warning(
                "Port requires root privileges",
                port=v,
                receiver=info.data.get("name", "unknown"),
            )
        return v

    @field_validator("protocol")
    @classmethod
    def validate_tls_config(cls, v: str, info) -> str:
        """Ensure TLS receivers have required certificate config."""
        if v == "tls":
            certfile = info.data.get("tls_certfile")
            keyfile = info.data.get("tls_keyfile")
            if not certfile or not keyfile:
                raise ValueError(
                    "TLS receivers require tls_certfile and tls_keyfile to be configured"
                )
        return v


class ReceiversConfigFile(BaseModel):
    """Receiver configuration file model.

    Attributes:
        receivers: List of receiver configurations
    """

    receivers: list[ReceiverConfigModel] = Field(
        default_factory=list, description="Receiver configurations"
    )


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    def __init__(self, errors: list[str]) -> None:
        """Initialize validation error.

        Args:
            errors: List of validation error messages
        """
        super().__init__("\n".join(errors))


def load_config_file(config_path: str | None = None) -> ReceiversConfigFile:
    """Load receiver configuration from a YAML file.

    Args:
        config_path: Path to config file. If not specified,
                    uses the default from settings.

    Returns:
        Parsed configuration file

    Raises:
        FileNotFoundError: If config file doesn't exist
        ConfigValidationError: If configuration is invalid
        yaml.YAMLError: If YAML parsing fails
        Exception: For other I/O errors
    """
    if config_path is None:
        # Check if a configured path exists
        config_file = Path(settings.receiver_config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        config_path = str(config_file)

    logger.info("Loading receiver configuration", path=config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data or "receivers" not in config_data:
            logger.warning("No receivers configured")
            return ReceiversConfigFile(receivers=[])

        # Create receiver instances
        for receiver_config in config_data["receivers"]:
            config = ReceiverConfigModel(**receiver_config)

            # Skip disabled receivers
            if not config.enabled:
                logger.debug("Skipping disabled receiver", name=config.name)
                continue

            # Create receiver (inline version for non-async use)
            if config.protocol == "udp":
                receiver = BatchUDPReceiver(
                    config,
                    batch_size=100,
                    batch_timeout=0.1,
                )
            elif config.protocol == "tcp":
                receiver = TCPReceiver(config)
            elif config.protocol == "tls":
                receiver = TCPReceiver(config)
            else:
                logger.warning(
                    "Unknown protocol, skipping",
                    name=config.name,
                    protocol=config.protocol,
                )
                return

            # Register message handler
            receiver.add_message_handler(self._handle_raw_message)

            # Initialize stats
            self._stats[config.name] = {
                "messages_received": 0,
                "last_message_time": None,
            }

            self._receivers[config.name] = receiver

        self._logger.info(
            "Receivers loaded",
            total=len(self._receivers),
            receivers=list(self._receivers.keys()),
        )

    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML", error=str(e))
        raise

    except Exception as e:
        logger.error("Failed to read configuration file", error=str(e))
        raise


def validate_config(config_data: dict[str, Any]) -> ReceiversConfigFile:
    """Validate configuration data.

    Args:
        config_data: Configuration dictionary

    Returns:
        Validated configuration file

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    try:
        return ReceiversConfigFile(**config_data)
    except Exception as e:
        errors = []
        if hasattr(e, "errors"):
            for error in e.errors():  # type: ignore
                loc = " -> ".join(str(p) for p in error["loc"])
                err_msg = error["msg"]
                errors.append(f"{loc}: {err_msg}")
        else:
            errors = [str(e)]

        logger.error("Configuration validation failed", errors=errors)
        raise ConfigValidationError(errors)


def resolve_file_path(file_path: str | None, relative_to: str | None) -> str | None:
    """Resolve a file path relative to a base directory.

    Args:
        file_path: File path to resolve (can be None)
        relative_to: Base directory for relative paths

    Returns:
            Resolved absolute path or None

    """
    if file_path is None:
        return None

    path = Path(file_path)

    if path.is_absolute():
        return str(path)

    # Resolve relative to config directory or specified directory
    if relative_to:
        base = Path(relative_to)
    else:
        base = settings.config_dir

    resolved = base / path
    return str(resolved.resolve())


def get_default_config() -> ReceiversConfigFile:
    """Get the default receiver configuration.

    Returns:
        Default configuration with common syslog receivers

    """
    return ReceiversConfigFile(
        receivers=[
            ReceiverConfigModel(
                name="standard_udp",
                protocol="udp",
                host="0.0.0.0",
                port=514,
                format="rfc5424",
                enabled=True,
                workers=4,
                buffer_size=1048576,  # 1MB
                batch_size=100,
                batch_timeout=0.1,
                description="Standard UDP Syslog receiver",
            ),
            ReceiverConfigModel(
                name="standard_tcp",
                protocol="tcp",
                host="0.0.0.0",
                port=514,
                format="rfc5424",
                enabled=True,
                workers=8,
                max_connections=1000,
                description="Standard TCP Syslog receiver",
            ),
            ReceiverConfigModel(
                name="firewall",
                protocol="tcp",
                host="0.0.0.0",
                port=514,
                format="cef",
                enabled=True,
                workers=4,
                max_connections=500,
                parser_options={
                    "device_type": "firewall",
                    "vendor": "generic",
                },
                description="Firewall CEF format receiver",
            ),
            ReceiverConfigModel(
                name="threat_probe",
                protocol="tcp",
                host="0.0.0.0",
                port=515,
                format="json",
                enabled=True,
                workers=4,
                max_connections=200,
                parser_options={
                    "device_type": "probe",
                    "vendor": "generic",
                },
                description="Threat probe JSON format receiver",
            ),
            ReceiverConfigModel(
                name="ids_ips",
                protocol="tcp",
                host="0.0.0.0",
                port=516,
                format="cef",
                enabled=True,
                workers=4,
                max_connections=200,
                parser_options={
                    "device_type": "ids",
                    "vendor": "generic",
                },
                description="IDS/IPS CEF format receiver",
            ),
        ]
    )


def generate_config_template(output_path: str | None = None) -> str:
    """Generate a configuration file template.

    Args:
        output_path: Path to write the template. If None, returns as string.

    Returns:
        YAML configuration template

    """
    template = """# Syslog Receiver Configuration
# 定义日志接收器的配置文件

receivers:
  # ========== Standard UDP Receiver ==========
  # 用于接收标准 Syslog 格式的 UDP 日志
  # 适用设备: 交换机、路由器、服务器
  - name: standard_udp
    protocol: udp
    host: 0.0.0.0
    port: 514
    format: rfc5424
    enabled: true
    workers: 4
    buffer_size: 1048576  # 1MB
    description: "标准 UDP Syslog 接收器，用于交换机、路由器等设备"

  # ========== Standard TCP Receiver ==========
  # 用于接收标准 Syslog 格式的 TCP 日志
  # 适用设备: 交换机、路由器、服务器
  - name: standard_tcp
    protocol: tcp
    host: 0.0.0.0
    port: 514
    format: rfc5424
    enabled: true
    workers: 8
    max_connections: 1000
    description: "标准 TCP Syslog 接收器，用于需要可靠传输的设备"

  # ========== Firewall Receiver (CEF) ==========
  # 用于接收防火墙的 CEF 格式日志
  # 适用设备: 深信服NGAF、天融信、Palo Alto 等
  - name: firewall
    protocol: tcp
    host: 0.0.0.0
    port: 514
    format: cef
    enabled: true
    workers: 4
    max_connections: 500
    parser_options:
      device_type: firewall
      vendor: generic
    description: "防火墙专用接收器，支持 CEF 格式"

  # ========== Threat Probe Receiver (JSON) ==========
  # 用于接收威胁探针的 JSON 格式日志
  # 适用设备: 奇安信天眼、深信服探针、科来分析器
  - name: threat_probe
    protocol: tcp
    host: 0.0.0.0
    port: 515
    format: json
    enabled: true
    workers: 4
    max_connections: 200
    parser_options:
      device_type: probe
      vendor: generic
    description: "威胁探针专用接收器，支持 JSON 格式"

  # ========== IDS/IPS Receiver (CEF) ==========
  # 用于接收 IDS/IPS 的 CEF 格式日志
  # 适用设备: 绿盟NIPS、启明星辰
  - name: ids_ips
    protocol: tcp
    host: 0.0.0.0
    port: 516
    format: cef
    enabled: true
    workers: 4
    max_connections: 200
    parser_options:
      device_type: ids
      vendor: generic
    description: "IDS/IPS专用接收器，支持 CEF 格式"

  # ========== Example: Huawei Switch (端口分离) ==========
  # 如果需要为不同品牌的设备使用不同端口，取消下面的注释
  # - name: huawei_switch
  #   protocol: udp
  #   host: 0.0.0.0
  #   port: 5514
  #   format: rfc5424
  #   enabled: false
  #   workers: 2
  #   parser_options:
  #     vendor: huawei
  #     device_type: switch
  #   description: "华为交换机专用端口"

  # ========== Example: Cisco Switch ==========
  # - name: cisco_switch
  #   protocol: udp
  #   host: 0.0.0.0
  #   port: 5515
  #   format: rfc5424
  #   enabled: false
  #   workers: 2
  #   parser_options:
  #     vendor: cisco
  #     device_type: switch
  #   description: "思科交换机专用端口"
"""

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(template, encoding="utf-8")
        logger.info("Configuration template written", path=str(output_file))
        return template

    return template
