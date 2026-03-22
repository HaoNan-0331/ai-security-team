"""
Threat Tagger for Syslog Server.

Detects and tags potential security threats in log entries.
Provides risk scoring and attack pattern detection.
"""

import asyncio
import ipaddress
import re
from collections import defaultdict
from dataclasses import dataclass, field as dc_field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from syslog_server.utils.logger import get_logger

logger = get_logger(__name__)


class ThreatCategory(str, Enum):
    """Threat category classifications."""

    MALWARE = "malware"
    PHISHING = "phishing"
    DOS = "dos"
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    RECONNAISSANCE = "reconnaissance"
    EXPLOIT = "exploit"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERSISTENCE = "persistence"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_THEFT = "credential_theft"
    RANSOMWARE = "ransomware"
    CRYPTO_MINING = "crypto_mining"
    BOTNET = "botnet"
    APT = "apt"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk level classifications."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ThreatSignature:
    """Threat detection signature."""

    id: str
    name: str
    category: ThreatCategory
    description: str
    patterns: list[str]  # Regex patterns
    field: str | None = None  # Field to match (None = any field)
    severity: int = 5  # Base severity contribution
    risk_score: int = 50  # Base risk score
    tags: list[str] = dc_field(default_factory=list)
    enabled: bool = True
    case_insensitive: bool = True


@dataclass
class ThreatMatch:
    """Threat match result."""

    signature_id: str
    signature_name: str
    category: ThreatCategory
    matched_pattern: str
    matched_text: str
    field: str | None
    risk_score: int


@dataclass
class ThreatDetectionResult:
    """Threat detection result."""

    detected: bool
    risk_score: int
    risk_level: RiskLevel
    categories: list[ThreatCategory]
    matches: list[ThreatMatch]
    tags: list[str]
    attack_patterns: list[str]


class IPReputation:
    """IP reputation checker."""

    # Known malicious IP ranges/indicators
    MALICIOUS_INDICATORS = {
        # Tor exit nodes patterns (simplified)
        "tor_exit": r".*tor.*",
        # Known botnet C2 patterns
        "botnet_c2": r".*botnet.*",
    }

    SUSPICIOUS_PORTS = {
        22: "ssh_brute_force",
        23: "telnet",
        135: "rpc",
        139: "netbios",
        445: "smb",
        1433: "mssql",
        1434: "mssql_monitor",
        3306: "mysql",
        3389: "rdp",
        5432: "postgresql",
        5900: "vnc",
        6379: "redis",
        27017: "mongodb",
    }

    # Known threat intelligence feeds (placeholder for integration)
    THREAT_FEEDS = []

    def __init__(self, config_path: str | Path | None = None):
        """Initialize IP reputation checker."""
        self.config_path = Path(config_path) if config_path else None
        self._malicious_ips: set[str] = set()
        self._suspicious_ips: set[str] = set()
        self._whitelist: set[str] = set()

    async def initialize(self) -> None:
        """Initialize the reputation checker."""
        if self.config_path and self.config_path.exists():
            await self._load_config()
        logger.info("IP reputation checker initialized")

    async def _load_config(self) -> None:
        """Load reputation configuration."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            self._malicious_ips = set(data.get("malicious_ips", []))
            self._suspicious_ips = set(data.get("suspicious_ips", []))
            self._whitelist = set(data.get("whitelist", []))

            # Load IP ranges
            for range_str in data.get("malicious_ranges", []):
                try:
                    network = ipaddress.ip_network(range_str, strict=False)
                    for ip in network.hosts():
                        self._malicious_ips.add(str(ip))
                except ValueError:
                    logger.warning("Invalid IP range", range=range_str)

        except Exception as e:
            logger.error("Failed to load reputation config", error=str(e))

    def check_ip(self, ip_address: str) -> dict[str, Any]:
        """
        Check IP reputation.

        Returns:
            Dictionary with reputation information
        """
        result = {
            "malicious": False,
            "suspicious": False,
            "whitelisted": False,
            "risk_score": 0,
            "tags": [],
        }

        if ip_address in self._whitelist:
            result["whitelisted"] = True
            return result

        if ip_address in self._malicious_ips:
            result["malicious"] = True
            result["risk_score"] = 100
            result["tags"].append("known_malicious")
            return result

        if ip_address in self._suspicious_ips:
            result["suspicious"] = True
            result["risk_score"] = 50
            result["tags"].append("suspicious")

        # Check for private IP
        try:
            addr = ipaddress.ip_address(ip_address)
            if addr.is_private:
                result["tags"].append("private_ip")
            elif addr.is_loopback:
                result["tags"].append("loopback")
            elif addr.is_link_local:
                result["tags"].append("link_local")
            elif addr.is_reserved:
                result["tags"].append("reserved")
            elif addr.is_multicast:
                result["tags"].append("multicast")
        except ValueError:
            pass

        return result

    def check_port(self, port: int) -> dict[str, Any]:
        """Check port reputation."""
        result = {"suspicious": False, "risk_score": 0, "tags": []}

        if port in self.SUSPICIOUS_PORTS:
            result["suspicious"] = True
            result["risk_score"] = 30
            result["tags"] = [f"port_{self.SUSPICIOUS_PORTS[port]}"]

        return result


class ThreatTagger:
    """
    Threat detection and tagging engine.

    Analyzes log entries for potential security threats and applies tags.
    """

    def __init__(
        self,
        signatures_path: str | Path | None = None,
        reputation_config: str | Path | None = None,
        risk_threshold: int = 30,
        batch_size: int = 100,
    ):
        """
        Initialize the threat tagger.

        Args:
            signatures_path: Path to threat signatures configuration
            reputation_config: Path to IP reputation configuration
            risk_threshold: Minimum risk score to apply threat tags
            batch_size: Batch size for bulk processing
        """
        self.signatures_path = Path(signatures_path) if signatures_path else None
        self.risk_threshold = risk_threshold
        self.batch_size = batch_size

        self._signatures: dict[str, ThreatSignature] = {}
        self._compiled_patterns: dict[str, list[tuple[re.Pattern, ThreatSignature]]] = {}
        self._reputation = IPReputation(reputation_config)

        self._stats = {
            "processed": 0,
            "threats_detected": 0,
            "matches_by_signature": defaultdict(int),
            "matches_by_category": defaultdict(int),
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the threat tagger."""
        await self._load_signatures()
        await self._reputation.initialize()
        self._initialized = True
        logger.info("Threat tagger initialized", signatures_count=len(self._signatures))

    async def _load_signatures(self) -> None:
        """Load threat signatures from configuration."""
        # Load default signatures
        self._add_default_signatures()

        # Load custom signatures from file
        if self.signatures_path and self.signatures_path.exists():
            try:
                with open(self.signatures_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for sig_data in data.get("signatures", []):
                    try:
                        sig = ThreatSignature(**sig_data)
                        self._signatures[sig.id] = sig
                    except Exception as e:
                        logger.warning("Failed to parse signature", signature=sig_data, error=str(e))

            except Exception as e:
                logger.error("Failed to load signatures file", error=str(e))

        # Compile regex patterns
        self._compile_patterns()

    def _add_default_signatures(self) -> None:
        """Add default threat detection signatures."""
        default_signatures = [
            # SQL Injection
            ThreatSignature(
                id="SQLI_001",
                name="SQL Injection - Union Based",
                category=ThreatCategory.SQL_INJECTION,
                description="Union-based SQL injection pattern",
                patterns=[
                    r"union\s+select",
                    r"'\s+or\s+'",
                    r"1\s*=\s*1",
                    r"admin'--",
                    r"' OR 1=1--",
                ],
                field="message",
                risk_score=90,
                tags=["sqli", "injection"],
            ),
            # XSS
            ThreatSignature(
                id="XSS_001",
                name="Cross-Site Scripting",
                category=ThreatCategory.XSS,
                description="XSS attack pattern",
                patterns=[
                    r"<script[^>]*>.*?</script>",
                    r"javascript:",
                    r"onerror\s*=",
                    r"onload\s*=",
                    r"<iframe[^>]*>",
                ],
                field="message",
                risk_score=70,
                tags=["xss", "web_attack"],
            ),
            # Command Injection
            ThreatSignature(
                id="CMD_001",
                name="Command Injection",
                category=ThreatCategory.COMMAND_INJECTION,
                description="Command injection pattern",
                patterns=[
                    r";\s*(ls|cat|whoami|id|pwd)",
                    r"\|\s*(ls|cat|whoami)",
                    r"`.*`",
                    r"\$\(.*\)",
                    r"&&\s*\w+",
                ],
                field="message",
                risk_score=95,
                tags=["command_injection", "rce"],
            ),
            # Brute Force
            ThreatSignature(
                id="BF_001",
                name="Brute Force Attack",
                category=ThreatCategory.BRUTE_FORCE,
                description="Multiple failed login attempts",
                patterns=[
                    r"failed\s+password",
                    r"authentication\s+failure",
                    r"login\s+failed",
                    r"invalid\s+(user|password|credentials)",
                    r"access\s+denied",
                ],
                field="message",
                risk_score=60,
                tags=["brute_force", "authentication"],
            ),
            # Reconnaissance
            ThreatSignature(
                id="REC_001",
                name="Network Reconnaissance",
                category=ThreatCategory.RECONNAISSANCE,
                description="Network scanning/probing activity",
                patterns=[
                    r"port\s+scan",
                    r"network\s+scan",
                    r"nmap",
                    r"masscan",
                    r"enumeration",
                ],
                field="message",
                risk_score=40,
                tags=["recon", "scanning"],
            ),
            # Malware
            ThreatSignature(
                id="MAL_001",
                name="Malware Connection",
                category=ThreatCategory.MALWARE,
                description="Known malware C2 communication",
                patterns=[
                    r"malware",
                    r"trojan",
                    r"virus",
                    r"ransomware",
                    r"botnet",
                ],
                field="message",
                risk_score=85,
                tags=["malware", "c2"],
            ),
            # Data Exfiltration
            ThreatSignature(
                id="EXF_001",
                name="Data Exfiltration",
                category=ThreatCategory.DATA_EXFILTRATION,
                description="Large data transfer or suspicious export",
                patterns=[
                    r"data\s+exfiltration",
                    r"unusual\s+data\s+transfer",
                    r"bulk\s+export",
                    r"large\s+download",
                ],
                field="message",
                risk_score=80,
                tags=["exfiltration", "data_breach"],
            ),
            # Lateral Movement
            ThreatSignature(
                id="LAT_001",
                name="Lateral Movement",
                category=ThreatCategory.LATERAL_MOVEMENT,
                description="Internal network propagation",
                patterns=[
                    r"pass\s+the\s+hash",
                    r"pass\s+the\s+ticket",
                    r"smb\s+session",
                    r"remote\s+execution",
                    r"psExec",
                ],
                field="message",
                risk_score=75,
                tags=["lateral_movement", "internal"],
            ),
            # DDoS
            ThreatSignature(
                id="DOS_001",
                name="DDoS Attack",
                category=ThreatCategory.DOS,
                description="Distributed denial of service pattern",
                patterns=[
                    r"ddos",
                    r"denial\s+of\s+service",
                    r"flood",
                    r"volumetric\s+attack",
                    r"amplification\s+attack",
                ],
                field="message",
                risk_score=90,
                tags=["ddos", "dos"],
            ),
            # Privilege Escalation
            ThreatSignature(
                id="PRIV_001",
                name="Privilege Escalation",
                category=ThreatCategory.PRIVILEGE_ESCALATION,
                description="Privilege escalation attempt",
                patterns=[
                    r"sudo.*without\s+password",
                    r"uid\s*=\s*0",
                    r"root\s+access",
                    r"privilege\s+escalation",
                    r"runas\s*/admin",
                ],
                field="message",
                risk_score=80,
                tags=["privilege_escalation", "escalation"],
            ),
        ]

        for sig in default_signatures:
            self._signatures[sig.id] = sig

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        # Group signatures by field
        for sig in self._signatures.values():
            if not sig.enabled:
                continue

            field = sig.field or "any"
            if field not in self._compiled_patterns:
                self._compiled_patterns[field] = []

            flags = re.IGNORECASE if sig.case_insensitive else 0

            for pattern in sig.patterns:
                try:
                    compiled = re.compile(pattern, flags)
                    self._compiled_patterns[field].append((compiled, sig))
                except re.error as e:
                    logger.warning("Invalid regex pattern", pattern=pattern, error=str(e))

    async def analyze(self, log: dict[str, Any]) -> ThreatDetectionResult:
        """
        Analyze a log entry for threats.

        Args:
            log: Log entry dictionary

        Returns:
            Threat detection result
        """
        if not self._initialized:
            await self.initialize()

        self._stats["processed"] += 1

        matches: list[ThreatMatch] = []
        categories = set()
        total_risk_score = 0
        all_tags = set()
        attack_patterns = []

        # Check IP reputation
        if log.get("src_ip"):
            ip_rep = self._reputation.check_ip(log["src_ip"])
            if ip_rep["risk_score"] > 0:
                total_risk_score += ip_rep["risk_score"]
                all_tags.update(ip_rep["tags"])

        # Check port reputation
        if log.get("dst_port"):
            port_rep = self._reputation.check_port(log["dst_port"])
            if port_rep["risk_score"] > 0:
                total_risk_score += port_rep["risk_score"]
                all_tags.update(port_rep["tags"])

        # Match signatures
        for field_name, patterns in self._compiled_patterns.items():
            if field_name != "any" and field_name not in log:
                continue

            text = ""
            if field_name == "any":
                # Search across all string fields
                for v in log.values():
                    if isinstance(v, str):
                        text += " " + v
            else:
                value = log.get(field_name)
                if value is None:
                    continue
                text = str(value)

            for pattern, sig in patterns:
                match = pattern.search(text)
                if match:
                    threat_match = ThreatMatch(
                        signature_id=sig.id,
                        signature_name=sig.name,
                        category=sig.category,
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(0),
                        field=field_name if field_name != "any" else None,
                        risk_score=sig.risk_score,
                    )
                    matches.append(threat_match)
                    categories.add(sig.category)
                    total_risk_score += sig.risk_score
                    all_tags.update(sig.tags)
                    attack_patterns.append(sig.name)

                    # Update stats
                    self._stats["matches_by_signature"][sig.id] += 1
                    self._stats["matches_by_category"][sig.category.value] += 1

        # Normalize risk score
        risk_score = min(100, total_risk_score)

        # Determine risk level
        risk_level = self._calculate_risk_level(risk_score)

        # Check if threat detected
        detected = risk_score >= self.risk_threshold or len(matches) > 0

        if detected:
            self._stats["threats_detected"] += 1

        return ThreatDetectionResult(
            detected=detected,
            risk_score=risk_score,
            risk_level=risk_level,
            categories=list(categories),
            matches=matches,
            tags=list(all_tags),
            attack_patterns=attack_patterns,
        )

    def _calculate_risk_level(self, score: int) -> RiskLevel:
        """Calculate risk level from score."""
        if score >= 90:
            return RiskLevel.CRITICAL
        elif score >= 70:
            return RiskLevel.HIGH
        elif score >= 50:
            return RiskLevel.MEDIUM
        elif score >= 30:
            return RiskLevel.LOW
        return RiskLevel.INFO

    async def enrich(self, log: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich a log entry with threat information.

        Args:
            log: Log entry dictionary

        Returns:
            Enriched log entry
        """
        result = await self.analyze(log)

        if result.detected:
            log["threat_detected"] = True
            log["risk_score"] = result.risk_score
            log["risk_level"] = result.risk_level.value
            log["threat_categories"] = [c.value for c in result.categories]

            if result.attack_patterns:
                existing_patterns = log.get("attack_patterns", [])
                log["attack_patterns"] = list(set(existing_patterns + result.attack_patterns))

            if result.tags:
                existing_tags = log.get("tags", [])
                log["tags"] = list(set(existing_tags + result.tags))

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

        results = []

        for i in range(0, len(logs), self.batch_size):
            batch = logs[i : i + self.batch_size]
            enriched_batch = await asyncio.gather(*[self.enrich(log) for log in batch])
            results.extend(enriched_batch)

        return results

    async def get_stats(self) -> dict[str, Any]:
        """Get tagger statistics."""
        return {
            "initialized": self._initialized,
            "signatures_count": len(self._signatures),
            "risk_threshold": self.risk_threshold,
            "stats": dict(self._stats),
            "matches_by_signature": dict(self._stats["matches_by_signature"]),
            "matches_by_category": dict(self._stats["matches_by_category"]),
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {
            "processed": 0,
            "threats_detected": 0,
            "matches_by_signature": defaultdict(int),
            "matches_by_category": defaultdict(int),
        }
