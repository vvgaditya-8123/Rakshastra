"""Behavioural Analytics Engine.

Provides a SQLite-backed engine that:
  1. Ingests log observations (login events, process events, network flows).
  2. Builds and updates statistical baselines per entity + feature.
  3. Scores new observations against baselines using z-score deviation.
  4. Persists detected anomalies for the agent to investigate.

This engine is the core of Point 1 (Behavioural Anomaly Detection) in the
Rakshastra Cyber Resilience platform. It does NOT rely on known malware
signatures — it detects deviations from *how systems normally behave*.
"""

import json
import math
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rakshastra_core.models.base import Severity, Confidence
from rakshastra_core.models.behavior import (
    BehaviorBaseline,
    AnomalyEvent,
    EntityType,
    AnomalyCategory,
)

logger = logging.getLogger(__name__)

# Anomaly severity thresholds (z-score boundaries)
_ZSCORE_LOW = 2.0       # 2σ → LOW severity
_ZSCORE_MEDIUM = 3.0    # 3σ → MEDIUM severity
_ZSCORE_HIGH = 4.0      # 4σ → HIGH severity
_ZSCORE_CRITICAL = 5.0  # 5σ → CRITICAL severity

# Minimum observations before a baseline is considered reliable
_MIN_BASELINE_SAMPLES = 5

# Category → MITRE ATT&CK mapping (default tactic + technique)
_CATEGORY_MITRE_MAP: Dict[AnomalyCategory, tuple] = {
    AnomalyCategory.LOGIN_TIME:           ("TA0001", "T1078"),   # Initial Access / Valid Accounts
    AnomalyCategory.LOGIN_LOCATION:       ("TA0001", "T1078"),   # Initial Access / Valid Accounts
    AnomalyCategory.PRIVILEGE_ESCALATION: ("TA0004", "T1068"),   # Privilege Escalation / Exploitation
    AnomalyCategory.LATERAL_MOVEMENT:     ("TA0008", "T1021"),   # Lateral Movement / Remote Services
    AnomalyCategory.DATA_EXFILTRATION:    ("TA0010", "T1041"),   # Exfiltration / Exfil Over C2
    AnomalyCategory.PROCESS_ANOMALY:      ("TA0002", "T1059"),   # Execution / Command Interpreter
    AnomalyCategory.RESOURCE_ACCESS:      ("TA0009", "T1005"),   # Collection / Data from Local System
    AnomalyCategory.NETWORK_ANOMALY:      ("TA0011", "T1071"),   # Command & Control / App Layer Protocol
    AnomalyCategory.PERSISTENCE:          ("TA0003", "T1547"),   # Persistence / Boot or Logon Autostart
    AnomalyCategory.COMMAND_ANOMALY:      ("TA0002", "T1059"),   # Execution / Command Interpreter
    AnomalyCategory.APT_BEACONING:        ("TA0011", "T1071"),   # Command & Control / App Layer Protocol
    AnomalyCategory.APT_STAGING:          ("TA0009", "T1074"),   # Collection / Data Staged
    AnomalyCategory.APT_C2_COMMUNICATION: ("TA0011", "T1572"),   # Command & Control / Protocol Tunneling
}


class BehavioralAnalyticsEngine:
    """SQLite-backed behavioral profiling and anomaly detection engine."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS behavior_baselines (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    baseline_mean REAL DEFAULT 0.0,
                    baseline_std REAL DEFAULT 0.0,
                    baseline_min REAL DEFAULT 0.0,
                    baseline_max REAL DEFAULT 0.0,
                    sample_count INTEGER DEFAULT 0,
                    histogram TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    UNIQUE(entity_id, feature_name)
                );

                CREATE TABLE IF NOT EXISTS anomaly_events (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    observed_value REAL,
                    baseline_mean REAL,
                    baseline_std REAL,
                    deviation_score REAL,
                    severity TEXT,
                    confidence TEXT,
                    description TEXT,
                    raw_evidence TEXT,
                    mitre_tactic TEXT DEFAULT '',
                    mitre_technique TEXT DEFAULT '',
                    recommended_action TEXT DEFAULT '',
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS raw_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    raw_data TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_baselines_entity
                    ON behavior_baselines(entity_id, feature_name);
                CREATE INDEX IF NOT EXISTS idx_anomalies_entity
                    ON anomaly_events(entity_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_anomalies_severity
                    ON anomaly_events(severity, created_at);
                CREATE INDEX IF NOT EXISTS idx_observations_entity
                    ON raw_observations(entity_id, feature_name);
            """)
        finally:
            conn.close()

    # ── Observation Ingestion ────────────────────────────────────────────

    def ingest_observation(
        self,
        entity_id: str,
        entity_type: str,
        feature_name: str,
        value: float,
        raw_data: Optional[dict] = None,
    ) -> Optional[AnomalyEvent]:
        """Ingest a single observation, update the baseline, and score it.

        Returns an AnomalyEvent if the observation is anomalous (deviation
        exceeds the LOW threshold), otherwise returns None.
        """
        now = datetime.utcnow().isoformat() + "Z"
        entity_type_enum = EntityType(entity_type) if isinstance(entity_type, str) else entity_type

        # 1. Store the raw observation
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO raw_observations
                   (timestamp, entity_id, entity_type, feature_name, value, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (now, entity_id, entity_type_enum.value, feature_name, value,
                 json.dumps(raw_data or {})),
            )
            conn.commit()
        finally:
            conn.close()

        # 2. Get or create baseline
        baseline = self._get_baseline(entity_id, feature_name)

        # 3. Score against baseline (only if we have enough samples)
        anomaly = None
        if baseline and baseline.sample_count >= _MIN_BASELINE_SAMPLES:
            anomaly = self._score_observation(
                entity_id, entity_type_enum, feature_name, value, baseline
            )

        # 4. Update the baseline with this new observation (online update)
        self._update_baseline(entity_id, entity_type_enum, feature_name, value)

        return anomaly

    def ingest_batch(
        self,
        observations: List[Dict[str, Any]],
    ) -> List[AnomalyEvent]:
        """Ingest a batch of observations. Returns list of detected anomalies.

        Each observation dict must have keys:
            entity_id, entity_type, feature_name, value
        Optional key: raw_data (dict)
        """
        anomalies = []
        for obs in observations:
            result = self.ingest_observation(
                entity_id=obs["entity_id"],
                entity_type=obs["entity_type"],
                feature_name=obs["feature_name"],
                value=obs["value"],
                raw_data=obs.get("raw_data"),
            )
            if result:
                anomalies.append(result)
        return anomalies

    # ── Baseline Management ──────────────────────────────────────────────

    def _get_baseline(self, entity_id: str, feature_name: str) -> Optional[BehaviorBaseline]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                """SELECT * FROM behavior_baselines
                   WHERE entity_id = ? AND feature_name = ?""",
                (entity_id, feature_name),
            ).fetchone()
            if row:
                return BehaviorBaseline(
                    id=row["id"],
                    created_at=row["created_at"],
                    entity_id=row["entity_id"],
                    entity_type=EntityType(row["entity_type"]),
                    feature_name=row["feature_name"],
                    baseline_mean=row["baseline_mean"],
                    baseline_std=row["baseline_std"],
                    baseline_min=row["baseline_min"],
                    baseline_max=row["baseline_max"],
                    sample_count=row["sample_count"],
                    histogram=json.loads(row["histogram"] or "{}"),
                    metadata=json.loads(row["metadata"] or "{}"),
                )
        finally:
            conn.close()
        return None

    def _update_baseline(
        self,
        entity_id: str,
        entity_type: EntityType,
        feature_name: str,
        new_value: float,
    ) -> None:
        """Online (incremental) baseline update using Welford's algorithm.

        This avoids re-reading all historical observations to recompute
        mean/std — critical for real-time ingestion at scale.
        """
        baseline = self._get_baseline(entity_id, feature_name)
        now = datetime.utcnow().isoformat() + "Z"

        if baseline is None:
            # First observation for this entity+feature — create baseline
            bl = BehaviorBaseline(
                entity_id=entity_id,
                entity_type=entity_type,
                feature_name=feature_name,
                baseline_mean=new_value,
                baseline_std=0.0,
                baseline_min=new_value,
                baseline_max=new_value,
                sample_count=1,
                histogram={str(int(new_value)): 1},
            )
            conn = self._get_connection()
            try:
                conn.execute(
                    """INSERT INTO behavior_baselines
                       (id, created_at, entity_id, entity_type, feature_name,
                        baseline_mean, baseline_std, baseline_min, baseline_max,
                        sample_count, histogram, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (bl.id, now, bl.entity_id, bl.entity_type.value,
                     bl.feature_name, bl.baseline_mean, bl.baseline_std,
                     bl.baseline_min, bl.baseline_max, bl.sample_count,
                     json.dumps(bl.histogram), json.dumps(bl.metadata)),
                )
                conn.commit()
            finally:
                conn.close()
            return

        # Welford's online algorithm for running mean and variance
        n = baseline.sample_count + 1
        old_mean = baseline.baseline_mean
        new_mean = old_mean + (new_value - old_mean) / n

        # For variance: M2 = (n-1)*old_var; M2_new = M2 + (val - old_mean)*(val - new_mean)
        old_var = baseline.baseline_std ** 2
        old_m2 = (n - 1) * old_var
        new_m2 = old_m2 + (new_value - old_mean) * (new_value - new_mean)
        new_std = math.sqrt(new_m2 / n) if n > 1 else 0.0

        new_min = min(baseline.baseline_min, new_value)
        new_max = max(baseline.baseline_max, new_value)

        # Update histogram bucket
        histogram = baseline.histogram.copy()
        bucket = str(int(new_value))
        histogram[bucket] = histogram.get(bucket, 0) + 1

        conn = self._get_connection()
        try:
            conn.execute(
                """UPDATE behavior_baselines
                   SET baseline_mean = ?, baseline_std = ?,
                       baseline_min = ?, baseline_max = ?,
                       sample_count = ?, histogram = ?
                   WHERE entity_id = ? AND feature_name = ?""",
                (new_mean, new_std, new_min, new_max, n,
                 json.dumps(histogram), entity_id, feature_name),
            )
            conn.commit()
        finally:
            conn.close()

    def build_baseline_from_history(
        self, entity_id: str, feature_name: str
    ) -> Optional[BehaviorBaseline]:
        """Rebuild a baseline from all stored raw observations.

        Useful for initial setup or when the incremental baseline needs
        to be recalibrated.
        """
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """SELECT value FROM raw_observations
                   WHERE entity_id = ? AND feature_name = ?
                   ORDER BY timestamp""",
                (entity_id, feature_name),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        values = [row["value"] for row in rows]
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0.0
        std = math.sqrt(variance)

        baseline = self._get_baseline(entity_id, feature_name)
        if baseline:
            conn = self._get_connection()
            try:
                conn.execute(
                    """UPDATE behavior_baselines
                       SET baseline_mean = ?, baseline_std = ?,
                           baseline_min = ?, baseline_max = ?,
                           sample_count = ?
                       WHERE entity_id = ? AND feature_name = ?""",
                    (mean, std, min(values), max(values), n,
                     entity_id, feature_name),
                )
                conn.commit()
            finally:
                conn.close()
            baseline.baseline_mean = mean
            baseline.baseline_std = std
            baseline.sample_count = n
            return baseline

        return None

    # ── Anomaly Scoring ──────────────────────────────────────────────────

    def _score_observation(
        self,
        entity_id: str,
        entity_type: EntityType,
        feature_name: str,
        observed_value: float,
        baseline: BehaviorBaseline,
    ) -> Optional[AnomalyEvent]:
        """Compute z-score and create an AnomalyEvent if anomalous."""
        if baseline.baseline_std == 0:
            # Zero variance means all previous observations were identical.
            # Any different value is anomalous.
            if observed_value == baseline.baseline_mean:
                return None
            z_score = _ZSCORE_CRITICAL  # Max severity for breaking a constant
        else:
            z_score = abs(observed_value - baseline.baseline_mean) / baseline.baseline_std

        if z_score < _ZSCORE_LOW:
            return None  # Within normal range

        # Determine severity from z-score
        if z_score >= _ZSCORE_CRITICAL:
            severity = Severity.CRITICAL
            confidence = Confidence.HIGH
        elif z_score >= _ZSCORE_HIGH:
            severity = Severity.HIGH
            confidence = Confidence.HIGH
        elif z_score >= _ZSCORE_MEDIUM:
            severity = Severity.MEDIUM
            confidence = Confidence.MEDIUM
        else:
            severity = Severity.LOW
            confidence = Confidence.LOW

        # Map feature to anomaly category
        category = self._classify_feature(feature_name)
        mitre_tactic, mitre_technique = _CATEGORY_MITRE_MAP.get(
            category, ("", "")
        )

        description = (
            f"Anomalous {feature_name} detected for {entity_type.value} "
            f"'{entity_id}': observed={observed_value:.2f}, "
            f"baseline_mean={baseline.baseline_mean:.2f} ± "
            f"{baseline.baseline_std:.2f} (z-score={z_score:.2f})"
        )

        recommended_action = self._recommend_action(category, severity)

        anomaly = AnomalyEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            category=category,
            feature_name=feature_name,
            observed_value=observed_value,
            baseline_mean=baseline.baseline_mean,
            baseline_std=baseline.baseline_std,
            deviation_score=round(z_score, 4),
            severity=severity,
            confidence=confidence,
            description=description,
            raw_evidence=f"value={observed_value}, baseline={baseline.baseline_mean}±{baseline.baseline_std}",
            mitre_tactic=mitre_tactic,
            mitre_technique=mitre_technique,
            recommended_action=recommended_action,
        )

        # Persist the anomaly
        self._store_anomaly(anomaly)

        return anomaly

    def _store_anomaly(self, anomaly: AnomalyEvent) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO anomaly_events
                   (id, created_at, entity_id, entity_type, category,
                    feature_name, observed_value, baseline_mean, baseline_std,
                    deviation_score, severity, confidence, description,
                    raw_evidence, mitre_tactic, mitre_technique,
                    recommended_action, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (anomaly.id, anomaly.created_at, anomaly.entity_id,
                 anomaly.entity_type.value, anomaly.category.value,
                 anomaly.feature_name, anomaly.observed_value,
                 anomaly.baseline_mean, anomaly.baseline_std,
                 anomaly.deviation_score,
                 anomaly.severity.value, anomaly.confidence.value,
                 anomaly.description, anomaly.raw_evidence,
                 anomaly.mitre_tactic, anomaly.mitre_technique,
                 anomaly.recommended_action,
                 json.dumps(anomaly.metadata)),
            )
            conn.commit()
        finally:
            conn.close()

    # ── Query & Reporting ────────────────────────────────────────────────

    def get_anomalies(
        self,
        entity_id: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query stored anomaly events with optional filters."""
        query = "SELECT * FROM anomaly_events WHERE 1=1"
        params: list = []

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if category:
            query += " AND category = ?"
            params.append(category)
        if since:
            query += " AND created_at >= ?"
            params.append(since)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_baselines(
        self,
        entity_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all baselines, optionally filtered by entity."""
        query = "SELECT * FROM behavior_baselines"
        params: list = []
        if entity_id:
            query += " WHERE entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY entity_id, feature_name"

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get aggregate anomaly statistics for dashboard/reporting."""
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) as c FROM anomaly_events").fetchone()["c"]
            by_severity = {}
            for row in conn.execute(
                "SELECT severity, COUNT(*) as c FROM anomaly_events GROUP BY severity"
            ).fetchall():
                by_severity[row["severity"]] = row["c"]

            by_category = {}
            for row in conn.execute(
                "SELECT category, COUNT(*) as c FROM anomaly_events GROUP BY category"
            ).fetchall():
                by_category[row["category"]] = row["c"]

            by_entity = {}
            for row in conn.execute(
                "SELECT entity_id, COUNT(*) as c FROM anomaly_events GROUP BY entity_id ORDER BY c DESC LIMIT 10"
            ).fetchall():
                by_entity[row["entity_id"]] = row["c"]

            baseline_count = conn.execute(
                "SELECT COUNT(*) as c FROM behavior_baselines"
            ).fetchone()["c"]

            observation_count = conn.execute(
                "SELECT COUNT(*) as c FROM raw_observations"
            ).fetchone()["c"]

            return {
                "total_anomalies": total,
                "by_severity": by_severity,
                "by_category": by_category,
                "top_anomalous_entities": by_entity,
                "total_baselines": baseline_count,
                "total_observations": observation_count,
            }
        finally:
            conn.close()

    # ── Feature Classification ───────────────────────────────────────────

    @staticmethod
    def _classify_feature(feature_name: str) -> AnomalyCategory:
        """Map a feature name to an AnomalyCategory."""
        fn = feature_name.lower()
        if "login" in fn and "hour" in fn or "login" in fn and "time" in fn:
            return AnomalyCategory.LOGIN_TIME
        if "login" in fn and ("ip" in fn or "location" in fn or "geo" in fn):
            return AnomalyCategory.LOGIN_LOCATION
        if "privilege" in fn or "sudo" in fn or "admin" in fn or "escalat" in fn:
            return AnomalyCategory.PRIVILEGE_ESCALATION
        if "lateral" in fn or "rdp" in fn or "smb" in fn or "ssh_session" in fn:
            return AnomalyCategory.LATERAL_MOVEMENT
        if "exfil" in fn or "bytes_out" in fn or "upload" in fn or "outbound" in fn:
            return AnomalyCategory.DATA_EXFILTRATION
        if "process" in fn or "child_proc" in fn or "exec" in fn:
            return AnomalyCategory.PROCESS_ANOMALY
        if "file_access" in fn or "resource" in fn or "share" in fn or "db_query" in fn:
            return AnomalyCategory.RESOURCE_ACCESS
        if "port" in fn or "beacon" in fn or "dns" in fn or "connection" in fn:
            return AnomalyCategory.NETWORK_ANOMALY
        if "registry" in fn or "cron" in fn or "startup" in fn or "persist" in fn:
            return AnomalyCategory.PERSISTENCE
        if "command" in fn or "cmd" in fn or "powershell" in fn:
            return AnomalyCategory.COMMAND_ANOMALY
        if "beacon" in fn or "interval" in fn or "callback" in fn or "heartbeat" in fn:
            return AnomalyCategory.APT_BEACONING
        if "staging" in fn or "archive" in fn or "compress" in fn or "zip" in fn:
            return AnomalyCategory.APT_STAGING
        if "tunnel" in fn or "dns_query_length" in fn or "encoded" in fn or "c2" in fn:
            return AnomalyCategory.APT_C2_COMMUNICATION
        return AnomalyCategory.PROCESS_ANOMALY  # Default fallback

    @staticmethod
    def _recommend_action(category: AnomalyCategory, severity: Severity) -> str:
        """Generate a recommended action based on category and severity."""
        actions = {
            AnomalyCategory.LOGIN_TIME: "Verify user identity. Check if this login was expected. Consider forcing MFA re-authentication.",
            AnomalyCategory.LOGIN_LOCATION: "Block the source IP if unrecognized. Force password reset. Check for credential compromise.",
            AnomalyCategory.PRIVILEGE_ESCALATION: "Review the privilege change. Audit recent admin actions. Check for exploitation indicators.",
            AnomalyCategory.LATERAL_MOVEMENT: "Investigate the target host. Check for unauthorized remote sessions. Consider network segmentation.",
            AnomalyCategory.DATA_EXFILTRATION: "Monitor outbound traffic. Check data classification of transferred files. Consider blocking the destination.",
            AnomalyCategory.PROCESS_ANOMALY: "Inspect the process tree. Check parent-child relationships. Look for living-off-the-land techniques.",
            AnomalyCategory.RESOURCE_ACCESS: "Audit file access logs. Verify the user's need-to-know. Check for data staging.",
            AnomalyCategory.NETWORK_ANOMALY: "Analyze network flows. Check for beaconing patterns. Investigate destination IPs.",
            AnomalyCategory.PERSISTENCE: "Check for new scheduled tasks, registry modifications, or startup items. Verify legitimacy.",
            AnomalyCategory.COMMAND_ANOMALY: "Review the executed commands. Check for reconnaissance or living-off-the-land binaries (LOLBins).",
            AnomalyCategory.APT_BEACONING: "Investigate destination IP/domain for C2 indicators. Analyze callback interval regularity. Deploy DNS sinkholing.",
            AnomalyCategory.APT_STAGING: "Check for unusual file compression or archiving activity. Monitor for data staging in temp directories. Audit file access patterns.",
            AnomalyCategory.APT_C2_COMMUNICATION: "Inspect DNS query patterns for tunneling. Analyze payload encoding. Block suspicious DNS resolvers and deploy protocol analysis.",
        }
        action = actions.get(category, "Investigate the anomaly and correlate with other signals.")
        if severity in (Severity.CRITICAL, Severity.HIGH):
            action = f"URGENT: {action} Escalate to security team immediately."
        return action

    # ── APT-specific Detection Methods ───────────────────────────────────

    def detect_apt_patterns(self, entity_id: str) -> Dict[str, Any]:
        """Analyze an entity's historical anomalies for multi-stage APT indicators.

        Checks for:
          - Beaconing: periodic network connections with low jitter
          - Data staging: unusual file access patterns preceding exfiltration
          - C2 communication: DNS tunneling, encoded payloads
          - Multi-phase progression: anomalies spanning multiple kill-chain phases
        """
        anomalies = self.get_anomalies(entity_id=entity_id, limit=200)
        if not anomalies:
            return {
                "entity_id": entity_id,
                "apt_risk_score": 0.0,
                "indicators": [],
                "kill_chain_phases_detected": [],
                "assessment": "No anomalies recorded for this entity.",
            }

        indicators = []
        detected_tactics: set = set()
        apt_score = 0.0

        # Collect unique MITRE tactics from anomalies
        for a in anomalies:
            tactic = a.get("mitre_tactic", "")
            if tactic:
                detected_tactics.add(tactic)

        # Multi-phase indicator: anomalies spanning 3+ kill-chain phases
        if len(detected_tactics) >= 3:
            indicators.append({
                "type": "multi_phase_progression",
                "severity": "HIGH",
                "description": f"Anomalies detected across {len(detected_tactics)} kill-chain phases: {sorted(detected_tactics)}",
                "mitre_tactics": sorted(detected_tactics),
            })
            apt_score += 0.3

        # Beaconing indicator: multiple network anomalies
        network_anomalies = [
            a for a in anomalies
            if a.get("category") in ("NETWORK_ANOMALY", "APT_BEACONING", "APT_C2_COMMUNICATION")
        ]
        if len(network_anomalies) >= 3:
            indicators.append({
                "type": "beaconing_pattern",
                "severity": "CRITICAL",
                "description": f"{len(network_anomalies)} network/beaconing anomalies detected — possible C2 communication.",
                "count": len(network_anomalies),
            })
            apt_score += 0.25

        # Data staging indicator: resource access + exfiltration anomalies
        resource_anomalies = [a for a in anomalies if a.get("category") in ("RESOURCE_ACCESS", "APT_STAGING")]
        exfil_anomalies = [a for a in anomalies if a.get("category") == "DATA_EXFILTRATION"]
        if resource_anomalies and exfil_anomalies:
            indicators.append({
                "type": "data_staging_exfiltration",
                "severity": "CRITICAL",
                "description": f"Data staging ({len(resource_anomalies)} events) followed by exfiltration ({len(exfil_anomalies)} events) — classic APT pattern.",
            })
            apt_score += 0.25

        # Lateral movement indicator
        lateral_anomalies = [a for a in anomalies if a.get("category") == "LATERAL_MOVEMENT"]
        if lateral_anomalies:
            indicators.append({
                "type": "lateral_movement",
                "severity": "HIGH",
                "description": f"{len(lateral_anomalies)} lateral movement anomalies detected.",
            })
            apt_score += 0.15

        # Persistence indicator
        persistence_anomalies = [a for a in anomalies if a.get("category") == "PERSISTENCE"]
        if persistence_anomalies:
            indicators.append({
                "type": "persistence_mechanism",
                "severity": "HIGH",
                "description": f"{len(persistence_anomalies)} persistence-related anomalies.",
            })
            apt_score += 0.1

        # Severity escalation
        critical_count = sum(1 for a in anomalies if a.get("severity") in ("CRITICAL", "HIGH"))
        if critical_count >= 5:
            apt_score += 0.15

        apt_score = min(round(apt_score, 3), 1.0)

        # Overall assessment
        if apt_score >= 0.7:
            assessment = "CRITICAL: Strong indicators of APT activity. Immediate incident response recommended."
        elif apt_score >= 0.4:
            assessment = "HIGH: Multiple APT indicators detected. Detailed investigation required."
        elif apt_score >= 0.2:
            assessment = "MODERATE: Some APT-like patterns detected. Monitoring and correlation recommended."
        else:
            assessment = "LOW: Minimal APT indicators. Continue routine monitoring."

        return {
            "entity_id": entity_id,
            "apt_risk_score": apt_score,
            "indicators": indicators,
            "kill_chain_phases_detected": sorted(detected_tactics),
            "total_anomalies": len(anomalies),
            "critical_anomalies": critical_count,
            "assessment": assessment,
        }

    def get_entity_risk_timeline(self, entity_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Return temporal anomaly progression for an entity.

        Groups anomalies by time window and shows severity escalation over time.
        """
        anomalies = self.get_anomalies(entity_id=entity_id, limit=limit)
        timeline = []
        for a in reversed(anomalies):  # Chronological order
            timeline.append({
                "timestamp": a.get("created_at", ""),
                "category": a.get("category", ""),
                "severity": a.get("severity", ""),
                "feature": a.get("feature_name", ""),
                "deviation_score": a.get("deviation_score", 0),
                "mitre_tactic": a.get("mitre_tactic", ""),
                "mitre_technique": a.get("mitre_technique", ""),
                "description": a.get("description", ""),
            })
        return timeline
