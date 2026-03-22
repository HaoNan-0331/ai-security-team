"""
MITRE ATT&CK Mapper for Syslog Server.

Maps security events and logs to MITRE ATT&CK framework.
Provides tactical and technical context for threat analysis.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from syslog_server.utils.logger import get_logger

logger = get_logger(__name__)


class MITRETactic(str, Enum):
    """MITRE ATT&CK Tactics (Enterprise)."""

    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


@dataclass
class MITRETechnique:
    """MITRE ATT&CK Technique."""

    id: str  # e.g., "T1190"
    name: str
    tactic: list[MITRETactic]
    description: str
    sub_techniques: list[str] = field(default_factory=list)
    detection: str | None = None
    references: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class MITREMapping:
    """Mapping rule for logs to MITRE techniques."""

    id: str
    name: str
    technique_id: str
    technique_name: str
    tactics: list[MITRETactic]
    patterns: dict[str, Any]  # Field patterns to match
    confidence: float = 1.0  # Mapping confidence (0-1)
    severity: int = 5
    tags: list[str] = field(default_factory=list)


@dataclass
class MITREMatch:
    """MITRE ATT&CK match result."""

    technique_id: str
    technique_name: str
    tactics: list[str]
    confidence: float
    matched_patterns: dict[str, Any]
    severity: int


class MITREMapper:
    """
    MITRE ATT&CK framework mapper.

    Maps log entries to MITRE ATT&CK tactics and techniques.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        confidence_threshold: float = 0.5,
        batch_size: int = 100,
    ):
        """
        Initialize the MITRE mapper.

        Args:
            config_path: Path to MITRE mapping configuration
            confidence_threshold: Minimum confidence to include mapping
            batch_size: Batch size for bulk processing
        """
        self.config_path = Path(config_path) if config_path else None
        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size

        self._techniques: dict[str, MITRETechnique] = {}
        self._mappings: list[MITREMapping] = []

        self._stats = {
            "processed": 0,
            "mapped": 0,
            "matches_by_technique": {},
            "matches_by_tactic": {},
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MITRE mapper."""
        await self._load_techniques()
        await self._load_mappings()
        self._initialized = True
        logger.info("MITRE mapper initialized", mappings_count=len(self._mappings))

    async def _load_techniques(self) -> None:
        """Load MITRE ATT&CK techniques."""
        # Load default techniques
        self._add_default_techniques()

        # Load custom techniques from file
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for tech_data in data.get("techniques", []):
                    try:
                        tech = MITRETechnique(**tech_data)
                        self._techniques[tech.id] = tech
                    except Exception as e:
                        logger.warning("Failed to parse technique", technique=tech_data, error=str(e))

            except Exception as e:
                logger.error("Failed to load techniques file", error=str(e))

    def _add_default_techniques(self) -> None:
        """Add default MITRE ATT&CK techniques."""
        default_techniques = [
            # Initial Access
            MITRETechnique(
                id="T1190",
                name="Exploit Public-Facing Application",
                tactic=[MITRETactic.INITIAL_ACCESS],
                description="Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program.",
                tags=["exploit", "web", "external"],
            ),
            MITRETechnique(
                id="T1078",
                name="Valid Accounts",
                tactic=[MITRETactic.INITIAL_ACCESS, MITRETactic.PRIVILEGE_ESCALATION, MITRETactic.DEFENSE_EVASION],
                description="Adversaries may obtain and abuse credentials of existing accounts.",
                tags=["credentials", "theft"],
            ),
            MITRETechnique(
                id="T1566",
                name="Phishing",
                tactic=[MITRETactic.INITIAL_ACCESS],
                description="Adversaries may send phishing messages to gain access to victim systems.",
                tags=["phishing", "social_engineering"],
            ),
            MITRETechnique(
                id="T1190",
                name="Exploit Public-Facing Application",
                tactic=[MITRETactic.INITIAL_ACCESS],
                description="Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program.",
                tags=["exploit", "vulnerability"],
            ),
            # Execution
            MITRETechnique(
                id="T1059",
                name="Command and Scripting Interpreter",
                tactic=[MITRETactic.EXECUTION],
                description="Adversaries may abuse command and script interpreters to execute commands.",
                tags=["command_line", "script"],
            ),
            MITRETechnique(
                id="T1203",
                name="Exploitation for Client Execution",
                tactic=[MITRETactic.EXECUTION, MITRETactic.PRIVILEGE_ESCALATION],
                description="Adversaries may exploit software vulnerabilities to execute code.",
                tags=["exploit", "vulnerability"],
            ),
            # Persistence
            MITRETechnique(
                id="T1543",
                name="Create or Modify System Process",
                tactic=[MITRETactic.PERSISTENCE, MITRETactic.PRIVILEGE_ESCALATION],
                description="Adversaries may create or modify system processes.",
                tags=["persistence", "process"],
            ),
            MITRETechnique(
                id="T1053",
                name="Scheduled Job/Task",
                tactic=[MITRETactic.PERSISTENCE, MITRETactic.PRIVILEGE_ESCALATION, MITRETactic.EXECUTION],
                description="Adversaries may abuse task scheduling functionality.",
                tags=["scheduler", "persistence"],
            ),
            MITRETechnique(
                id="T1547",
                name="Boot or Logon Autostart Execution",
                tactic=[MITRETactic.PERSISTENCE, MITRETactic.PRIVILEGE_ESCALATION],
                description="Adversaries may configure system settings to execute programs during boot.",
                tags=["autostart", "persistence"],
            ),
            # Credential Access
            MITRETechnique(
                id="T1003",
                name="OS Credential Dumping",
                tactic=[MITRETactic.CREDENTIAL_ACCESS],
                description="Adversaries may attempt to dump credentials.",
                tags=["credentials", "dumping"],
            ),
            MITRETechnique(
                id="T1110",
                name="Brute Force",
                tactic=[MITRETactic.CREDENTIAL_ACCESS, MITRETactic.INITIAL_ACCESS, MITRETactic.PERSISTENCE],
                description="Adversaries may use brute force techniques.",
                tags=["brute_force", "credentials"],
            ),
            MITRETechnique(
                id="T1552",
                name="Unsecured Credentials",
                tactic=[MITRETactic.CREDENTIAL_ACCESS],
                description="Adversaries may search for insecurely stored credentials.",
                tags=["credentials", "discovery"],
            ),
            # Discovery
            MITRETechnique(
                id="T1018",
                name="Remote System Discovery",
                tactic=[MITRETactic.DISCOVERY],
                description="Adversaries may attempt to get a listing of other systems.",
                tags=["discovery", "network"],
            ),
            MITRETechnique(
                id="T1087",
                name="Account Discovery",
                tactic=[MITRETactic.DISCOVERY],
                description="Adversaries may attempt to get a listing of accounts.",
                tags=["discovery", "accounts"],
            ),
            MITRETechnique(
                id="T1033",
                name="System Owner/User Discovery",
                tactic=[MITRETactic.DISCOVERY],
                description="Adversaries may attempt to identify the primary user.",
                tags=["discovery", "user"],
            ),
            MITRETechnique(
                id="T1069",
                name="Permission Groups Discovery",
                tactic=[MITRETactic.DISCOVERY],
                description="Adversaries may attempt to find group and permission settings.",
                tags=["discovery", "permissions"],
            ),
            # Lateral Movement
            MITRETechnique(
                id="T1021",
                name="Remote Services",
                tactic=[MITRETactic.LATERAL_MOVEMENT],
                description="Adversaries may use remote services to move between systems.",
                tags=["lateral_movement", "remote"],
            ),
            MITRETechnique(
                id="T1077",
                name="Windows Admin Shares",
                tactic=[MITRETactic.LATERAL_MOVEMENT],
                description="Adversaries may use admin shares for lateral movement.",
                tags=["lateral_movement", "smb"],
            ),
            MITRETechnique(
                id="T1563",
                name="Remote Service Session Hijacking",
                tactic=[MITRETactic.LATERAL_MOVEMENT],
                description="Adversaries may hijack a session.",
                tags=["lateral_movement", "session"],
            ),
            # Collection
            MITRETechnique(
                id="T1005",
                name="Data from Local System",
                tactic=[MITRETactic.COLLECTION],
                description="Adversaries may search local system sources.",
                tags=["collection", "local"],
            ),
            MITRETechnique(
                id="T1113",
                name="Screen Capture",
                tactic=[MITRETactic.COLLECTION],
                description="Adversaries may attempt to capture screen information.",
                tags=["collection", "screenshot"],
            ),
            # Command and Control
            MITRETechnique(
                id="T1071",
                name="Application Layer Protocol",
                tactic=[MITRETactic.COMMAND_AND_CONTROL],
                description="Adversaries may communicate using application layer protocols.",
                tags=["c2", "protocol"],
            ),
            MITRETechnique(
                id="T1095",
                name="Non-Application Layer Protocol",
                tactic=[MITRETactic.COMMAND_AND_CONTROL],
                description="Adversaries may use non-application layer protocols.",
                tags=["c2", "protocol"],
            ),
            MITRETechnique(
                id="T1102",
                name="Web Service",
                tactic=[MITRETactic.COMMAND_AND_CONTROL],
                description="Adversaries may use web services for command and control.",
                tags=["c2", "web"],
            ),
            # Exfiltration
            MITRETechnique(
                id="T1041",
                name="Exfiltration Over C2 Channel",
                tactic=[MITRETactic.EXFILTRATION],
                description="Adversaries may steal data by exfiltrating it over C2 channel.",
                tags=["exfiltration", "c2"],
            ),
            MITRETechnique(
                id="T1567",
                name="Exfiltration Over Web Service",
                tactic=[MITRETactic.EXFILTRATION],
                description="Adversaries may exfiltrate data using web services.",
                tags=["exfiltration", "web"],
            ),
            # Impact
            MITRETechnique(
                id="T1486",
                name="Data Encrypted for Impact",
                tactic=[MITRETactic.IMPACT],
                description="Adversaries may encrypt data on target systems.",
                tags=["ransomware", "impact"],
            ),
            MITRETechnique(
                id="T1485",
                name="Data Destruction",
                tactic=[MITRETactic.IMPACT],
                description="Adversaries may destroy data.",
                tags=["destruction", "impact"],
            ),
            MITRETechnique(
                id="T1498",
                name="Network Denial of Service",
                tactic=[MITRETactic.IMPACT],
                description="Adversaries may perform network denial of service.",
                tags=["dos", "impact"],
            ),
            # Defense Evasion
            MITRETechnique(
                id="T1564",
                name="Hide Artifacts",
                tactic=[MITRETactic.DEFENSE_EVASION],
                description="Adversaries may attempt to hide artifacts.",
                tags=["evasion", "hidden"],
            ),
            MITRETechnique(
                id="T1622",
                name="Debugger Evasion",
                tactic=[MITRETactic.DEFENSE_EVASION],
                description="Adversaries may use debugger evasion techniques.",
                tags=["evasion", "debugger"],
            ),
        ]

        for tech in default_techniques:
            self._techniques[tech.id] = tech

    async def _load_mappings(self) -> None:
        """Load MITRE mapping rules."""
        # Add default mappings
        self._add_default_mappings()

        # Load custom mappings from file
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for mapping_data in data.get("mappings", []):
                    try:
                        mapping = self._parse_mapping(mapping_data)
                        if mapping:
                            self._mappings.append(mapping)
                    except Exception as e:
                        logger.warning("Failed to parse mapping", mapping=mapping_data, error=str(e))

            except Exception as e:
                logger.error("Failed to load mappings file", error=str(e))

    def _add_default_mappings(self) -> None:
        """Add default MITRE mapping rules."""
        default_mappings = [
            # SQL Injection
            MITREMapping(
                id="MAP_SQli",
                name="SQL Injection Pattern",
                technique_id="T1190",
                technique_name="Exploit Public-Facing Application",
                tactics=[MITRETactic.INITIAL_ACCESS, MITRETactic.EXECUTION],
                patterns={
                    "message": ["union select", "' or '1'='1", "1=1", "admin'--", "drop table", "insert into"],
                },
                confidence=0.9,
                severity=8,
                tags=["web", "injection"],
            ),
            # Brute Force
            MITREMapping(
                id="MAP_BRUTE",
                name="Brute Force Login",
                technique_id="T1110",
                technique_name="Brute Force",
                tactics=[MITRETactic.CREDENTIAL_ACCESS, MITRETactic.INITIAL_ACCESS],
                patterns={
                    "message": ["failed password", "authentication failure", "invalid user", "login failed"],
                    "event_type": ["login", "authentication"],
                },
                confidence=0.85,
                severity=6,
                tags=["credentials"],
            ),
            # Port Scan
            MITREMapping(
                id="MAP_SCAN",
                name="Network Scanning",
                technique_id="T1018",
                technique_name="Remote System Discovery",
                tactics=[MITRETactic.DISCOVERY, MITRETactic.RECONNAISSANCE],
                patterns={
                    "message": ["port scan", "network scan", "nmap", "masscan"],
                    "event_type": ["scan", "recon"],
                },
                confidence=0.8,
                severity=4,
                tags=["recon", "network"],
            ),
            # Command Execution
            MITREMapping(
                id="MAP_CMD",
                name="Command Execution",
                technique_id="T1059",
                technique_name="Command and Scripting Interpreter",
                tactics=[MITRETactic.EXECUTION],
                patterns={
                    "message": ["; ls", "; cat", "&& whoami", "| id", "`whoami`", "$(id)"],
                    "event_type": ["command", "shell"],
                },
                confidence=0.85,
                severity=7,
                tags=["execution", "shell"],
            ),
            # Lateral Movement via SMB
            MITREMapping(
                id="MAP_SMB",
                name="SMB Lateral Movement",
                technique_id="T1021",
                technique_name="Remote Services",
                tactics=[MITRETactic.LATERAL_MOVEMENT],
                patterns={
                    "protocol": ["SMB", "smb", "445"],
                    "dst_port": [445],
                    "event_type": ["smb", "share", "admin"],
                },
                confidence=0.7,
                severity=6,
                tags=["lateral", "smb"],
            ),
            # RDP Lateral Movement
            MITREMapping(
                id="MAP_RDP",
                name="RDP Lateral Movement",
                technique_id="T1021",
                technique_name="Remote Services",
                tactics=[MITRETactic.LATERAL_MOVEMENT],
                patterns={
                    "protocol": ["RDP", "rdp"],
                    "dst_port": [3389],
                    "event_type": ["rdp", "remote", "desktop"],
                },
                confidence=0.75,
                severity=6,
                tags=["lateral", "rdp"],
            ),
            # Data Exfiltration
            MITREMapping(
                id="MAP_EXFIL",
                name="Data Exfiltration",
                technique_id="T1567",
                technique_name="Exfiltration Over Web Service",
                tactics=[MITRETactic.EXFILTRATION],
                patterns={
                    "message": ["data exfiltration", "unusual transfer", "bulk export"],
                    "event_type": ["exfil", "export", "upload"],
                },
                confidence=0.8,
                severity=8,
                tags=["exfil", "data"],
            ),
            # Ransomware
            MITREMapping(
                id="MAP_RANSOM",
                name="Ransomware Activity",
                technique_id="T1486",
                technique_name="Data Encrypted for Impact",
                tactics=[MITRETactic.IMPACT],
                patterns={
                    "message": ["ransomware", "encrypt", "decrypt notice", "bitcoin", "monero"],
                    "event_type": ["ransomware", "encryption"],
                },
                confidence=0.9,
                severity=10,
                tags=["ransomware", "impact"],
            ),
            # DDoS
            MITREMapping(
                id="MAP_DOS",
                name="DDoS Attack",
                technique_id="T1498",
                technique_name="Network Denial of Service",
                tactics=[MITRETactic.IMPACT],
                patterns={
                    "message": ["ddos", "denial of service", "flood", "volumetric"],
                    "event_type": ["ddos", "dos"],
                },
                confidence=0.85,
                severity=8,
                tags=["dos", "impact"],
            ),
            # Credential Dumping
            MITREMapping(
                id="MAP_DUMP",
                name="Credential Dumping",
                technique_id="T1003",
                technique_name="OS Credential Dumping",
                tactics=[MITRETactic.CREDENTIAL_ACCESS],
                patterns={
                    "message": ["credential dump", "lsa", "sam", "ntds.dit", "mimikatz", "password hash"],
                    "event_type": ["credential", "dump"],
                },
                confidence=0.9,
                severity=8,
                tags=["credentials", "dump"],
            ),
            # Scheduled Task Persistence
            MITREMapping(
                id="MAP_SCHED",
                name="Scheduled Task Persistence",
                technique_id="T1053",
                technique_name="Scheduled Job/Task",
                tactics=[MITRETactic.PERSISTENCE],
                patterns={
                    "message": ["scheduled task", "crontab", "at.exe", "schtasks"],
                    "event_type": ["schedule", "task", "cron"],
                },
                confidence=0.75,
                severity=6,
                tags=["persistence", "task"],
            ),
            # Pass-the-Hash
            MITREMapping(
                id="MAP_PTH",
                name="Pass the Hash",
                technique_id="T1550.002",
                technique_name="Pass the Hash",
                tactics=[MITRETactic.LATERAL_MOVEMENT, MITRETactic.CREDENTIAL_ACCESS],
                patterns={
                    "message": ["pass the hash", "pth", "overpass-the-hash", "ptt"],
                    "event_type": ["pth", "lateral"],
                },
                confidence=0.85,
                severity=8,
                tags=["lateral", "credentials"],
            ),
            # Webshell
            MITREMapping(
                id="MAP_WEBSHELL",
                name="Webshell Detection",
                technique_id="T1505",
                technique_name="Server Software Component",
                tactics=[MITRETactic.PERSISTENCE, MITRETactic.EXECUTION],
                patterns={
                    "message": ["webshell", "eval(", "system(", "exec(", "passthru("],
                    "event_type": ["webshell", "web"],
                },
                confidence=0.85,
                severity=9,
                tags=["webshell", "web", "persistence"],
            ),
            # DNS Tunneling
            MITREMapping(
                id="MAP_DNS_TUNNEL",
                name="DNS Tunneling",
                technique_id="T1071",
                technique_name="Application Layer Protocol",
                tactics=[MITRETactic.COMMAND_AND_CONTROL],
                patterns={
                    "protocol": ["DNS", "dns"],
                    "message": ["dns tunnel", "long dns query", "dns txt"],
                },
                confidence=0.7,
                severity=6,
                tags=["c2", "dns"],
            ),
        ]

        self._mappings.extend(default_mappings)

    def _parse_mapping(self, data: dict[str, Any]) -> MITREMapping | None:
        """Parse a mapping rule from configuration."""
        try:
            tactics_str = data.get("tactics", [])
            tactics = []

            for t in tactics_str:
                try:
                    tactics.append(MITRETactic(t))
                except ValueError:
                    logger.warning("Invalid tactic", tactic=t)

            if not tactics:
                return None

            return MITREMapping(
                id=data["id"],
                name=data["name"],
                technique_id=data["technique_id"],
                technique_name=data.get("technique_name", ""),
                tactics=tactics,
                patterns=data.get("patterns", {}),
                confidence=data.get("confidence", 0.5),
                severity=data.get("severity", 5),
                tags=data.get("tags", []),
            )
        except KeyError as e:
            logger.warning("Missing required field in mapping", error=str(e))
            return None

    async def map(self, log: dict[str, Any]) -> list[MITREMatch]:
        """
        Map a log entry to MITRE ATT&CK techniques.

        Args:
            log: Log entry dictionary

        Returns:
            List of MITRE matches
        """
        if not self._initialized:
            await self.initialize()

        self._stats["processed"] += 1

        matches: list[MITREMatch] = []

        for mapping in self._mappings:
            if mapping.confidence < self.confidence_threshold:
                continue

            match_result = self._check_mapping(log, mapping)
            if match_result:
                matches.append(match_result)

        if matches:
            self._stats["mapped"] += 1
            for match in matches:
                technique_id = match.technique_id
                tactic_key = ",".join(match.tactics)

                self._stats["matches_by_technique"][technique_id] = (
                    self._stats["matches_by_technique"].get(technique_id, 0) + 1
                )
                self._stats["matches_by_tactic"][tactic_key] = (
                    self._stats["matches_by_tactic"].get(tactic_key, 0) + 1
                )

        return matches

    def _check_mapping(self, log: dict[str, Any], mapping: MITREMapping) -> MITREMatch | None:
        """Check if a log entry matches a mapping rule."""
        matched_patterns = {}

        for field, patterns in mapping.patterns.items():
            if not isinstance(patterns, list):
                patterns = [patterns]

            field_value = log.get(field)
            if field_value is None:
                continue

            field_value = str(field_value).lower()

            for pattern in patterns:
                pattern_lower = str(pattern).lower()
                if pattern_lower in field_value:
                    matched_patterns[field] = pattern
                    break

        if matched_patterns:
            return MITREMatch(
                technique_id=mapping.technique_id,
                technique_name=mapping.technique_name,
                tactics=[t.value for t in mapping.tactics],
                confidence=mapping.confidence,
                matched_patterns=matched_patterns,
                severity=mapping.severity,
            )

        return None

    async def enrich(self, log: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich a log entry with MITRE ATT&CK information.

        Args:
            log: Log entry dictionary

        Returns:
            Enriched log entry
        """
        matches = await self.map(log)

        if matches:
            # Extract technique IDs and names
            technique_ids = [m.technique_id for m in matches]
            technique_names = [m.technique_name for m in matches]

            # Extract tactics
            all_tactics = set()
            for match in matches:
                all_tactics.update(match.tactics)

            # Get highest severity
            max_severity = max((m.severity for m in matches), default=5)

            # Add MITRE fields to log
            log["mitre_techniques"] = technique_ids
            log["mitre_technique_names"] = technique_names
            log["mitre_tactics"] = list(all_tactics)

            # Add to attack patterns if not present
            existing_patterns = log.get("attack_patterns", [])
            new_patterns = list(set(existing_patterns + technique_names))
            log["attack_patterns"] = new_patterns

            # Update risk score based on MITRE severity
            current_risk = log.get("risk_score", 0)
            log["risk_score"] = max(current_risk, max_severity * 10)

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
        """Get mapper statistics."""
        return {
            "initialized": self._initialized,
            "techniques_count": len(self._techniques),
            "mappings_count": len(self._mappings),
            "confidence_threshold": self.confidence_threshold,
            "stats": dict(self._stats),
        }

    def get_technique(self, technique_id: str) -> MITRETechnique | None:
        """Get technique details by ID."""
        return self._techniques.get(technique_id)

    def list_techniques(self) -> list[MITRETechnique]:
        """List all available techniques."""
        return list(self._techniques.values())
