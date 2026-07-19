"""SOAR Engine — Security Orchestration, Automation and Response.

Manages incident response playbooks, creates incidents from alert data,
and orchestrates (simulated or automated) response actions.
"""

import datetime
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Built-in Playbooks ──────────────────────────────────────────────────

_BUILTIN_PLAYBOOKS: List[Dict[str, Any]] = [
    {
        "id": "PB-001",
        "name": "Ransomware Response",
        "description": "Immediate response to ransomware detection including host isolation, account lockdown, and evidence preservation.",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "apt_tactics": ["TA0040", "TA0010"],
        "actions": [
            {"step": 1, "action": "Isolate affected host from network", "type": "containment", "automated": True},
            {"step": 2, "action": "Disable compromised user account", "type": "containment", "automated": True},
            {"step": 3, "action": "Snapshot affected disk for forensic analysis", "type": "evidence", "automated": False},
            {"step": 4, "action": "Block ransomware C2 IP addresses at perimeter firewall", "type": "containment", "automated": True},
            {"step": 5, "action": "Scan all endpoints for ransomware indicators", "type": "detection", "automated": True},
            {"step": 6, "action": "Verify backup integrity and initiate recovery", "type": "recovery", "automated": False},
            {"step": 7, "action": "Notify SOC and management", "type": "notification", "automated": True},
            {"step": 8, "action": "File incident report with CERT-In within 6 hours", "type": "compliance", "automated": False},
        ],
    },
    {
        "id": "PB-002",
        "name": "Credential Compromise Response",
        "description": "Response to detected credential theft or unauthorized access using stolen credentials.",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "apt_tactics": ["TA0006", "TA0001"],
        "actions": [
            {"step": 1, "action": "Force password reset for compromised accounts", "type": "containment", "automated": True},
            {"step": 2, "action": "Revoke all active sessions and tokens", "type": "containment", "automated": True},
            {"step": 3, "action": "Enable MFA on affected accounts", "type": "hardening", "automated": False},
            {"step": 4, "action": "Review authentication logs for unauthorized access", "type": "investigation", "automated": True},
            {"step": 5, "action": "Check for lateral movement from compromised account", "type": "investigation", "automated": True},
            {"step": 6, "action": "Rotate service account credentials", "type": "remediation", "automated": False},
            {"step": 7, "action": "Deploy credential monitoring on Dark Web feeds", "type": "monitoring", "automated": True},
        ],
    },
    {
        "id": "PB-003",
        "name": "Lateral Movement Detected",
        "description": "Response to detected lateral movement activity across the network.",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "apt_tactics": ["TA0008", "TA0007"],
        "actions": [
            {"step": 1, "action": "Segment affected network zone", "type": "containment", "automated": True},
            {"step": 2, "action": "Block RDP and SMB between workstation subnets", "type": "containment", "automated": True},
            {"step": 3, "action": "Deploy honeypot services on affected segment", "type": "deception", "automated": False},
            {"step": 4, "action": "Collect memory dumps from affected hosts", "type": "evidence", "automated": False},
            {"step": 5, "action": "Run EDR sweep for lateral movement tools (PsExec, Mimikatz, Cobalt Strike)", "type": "detection", "automated": True},
            {"step": 6, "action": "Map full attack path via infrastructure graph", "type": "investigation", "automated": True},
            {"step": 7, "action": "Revoke compromised credentials identified in the path", "type": "remediation", "automated": True},
        ],
    },
    {
        "id": "PB-004",
        "name": "Data Exfiltration Response",
        "description": "Response to detected or suspected data exfiltration activity.",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "apt_tactics": ["TA0010", "TA0009"],
        "actions": [
            {"step": 1, "action": "Block outbound connection to exfiltration destination IP/domain", "type": "containment", "automated": True},
            {"step": 2, "action": "Quarantine the source endpoint", "type": "containment", "automated": True},
            {"step": 3, "action": "Preserve network flow logs and proxy logs", "type": "evidence", "automated": True},
            {"step": 4, "action": "Identify and classify exfiltrated data", "type": "investigation", "automated": False},
            {"step": 5, "action": "Review DLP alerts for past 30 days", "type": "investigation", "automated": True},
            {"step": 6, "action": "Notify data protection officer and legal team", "type": "notification", "automated": True},
            {"step": 7, "action": "Assess regulatory notification requirements (DPDPA/GDPR)", "type": "compliance", "automated": False},
        ],
    },
    {
        "id": "PB-005",
        "name": "APT Persistence Removal",
        "description": "Systematic removal of APT persistence mechanisms after attribution.",
        "severity_trigger": ["CRITICAL"],
        "apt_tactics": ["TA0003", "TA0005"],
        "actions": [
            {"step": 1, "action": "Remove unauthorized scheduled tasks and cron jobs", "type": "remediation", "automated": True},
            {"step": 2, "action": "Clean malicious registry Run/RunOnce keys", "type": "remediation", "automated": True},
            {"step": 3, "action": "Remove unauthorized services and drivers", "type": "remediation", "automated": False},
            {"step": 4, "action": "Delete web shells from web servers", "type": "remediation", "automated": True},
            {"step": 5, "action": "Reset compromised SSH keys and certificates", "type": "remediation", "automated": False},
            {"step": 6, "action": "Re-image compromised hosts if persistence is extensive", "type": "recovery", "automated": False},
            {"step": 7, "action": "Deploy enhanced monitoring on cleaned hosts for 30 days", "type": "monitoring", "automated": True},
            {"step": 8, "action": "Verify all persistence mechanisms are removed via re-scan", "type": "verification", "automated": True},
        ],
    },
    {
        "id": "PB-006",
        "name": "Phishing Campaign Response",
        "description": "Response to detected phishing campaign targeting organisation users.",
        "severity_trigger": ["HIGH", "MEDIUM"],
        "apt_tactics": ["TA0001"],
        "actions": [
            {"step": 1, "action": "Block sender domain at email gateway", "type": "containment", "automated": True},
            {"step": 2, "action": "Quarantine all emails from the campaign", "type": "containment", "automated": True},
            {"step": 3, "action": "Identify users who clicked/opened malicious content", "type": "investigation", "automated": True},
            {"step": 4, "action": "Force password reset for affected users", "type": "remediation", "automated": True},
            {"step": 5, "action": "Scan endpoints of affected users for malware", "type": "detection", "automated": True},
            {"step": 6, "action": "Block phishing URLs at web proxy", "type": "containment", "automated": True},
            {"step": 7, "action": "Send awareness notification to all users", "type": "notification", "automated": True},
        ],
    },
]


class SOAREngine:
    """Security Orchestration, Automation and Response engine."""

    def __init__(self, db_path):
        if db_path == ":memory:":
            self.db_path = db_path
        else:
            self.db_path = str(Path(db_path))
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS soar_incidents (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'OPEN',
                    attributed_apt TEXT DEFAULT '',
                    alert_data TEXT DEFAULT '{}',
                    playbook_id TEXT DEFAULT '',
                    mode TEXT DEFAULT 'simulate',
                    assigned_to TEXT DEFAULT '',
                    resolution TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS soar_action_log (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    action_description TEXT NOT NULL,
                    action_type TEXT DEFAULT '',
                    status TEXT DEFAULT 'PENDING',
                    result TEXT DEFAULT '',
                    automated INTEGER DEFAULT 0,
                    executed_by TEXT DEFAULT 'system'
                );

                CREATE INDEX IF NOT EXISTS idx_actions_incident
                    ON soar_action_log(incident_id);
                CREATE INDEX IF NOT EXISTS idx_incidents_status
                    ON soar_incidents(status);
            """)
        finally:
            conn.close()

    # ── Playbook Management ──────────────────────────────────────────────

    def get_playbooks(self) -> List[Dict[str, Any]]:
        """Return all available playbooks."""
        return _BUILTIN_PLAYBOOKS

    def get_playbook(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Return a specific playbook by ID."""
        for pb in _BUILTIN_PLAYBOOKS:
            if pb["id"] == playbook_id:
                return pb
        return None

    def select_playbook(self, severity: str, tactics: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Auto-select the most appropriate playbook based on severity and tactics."""
        candidates = []
        for pb in _BUILTIN_PLAYBOOKS:
            # Check severity match
            if severity.upper() not in pb["severity_trigger"]:
                continue

            # Check tactic match
            score = 0
            if tactics:
                overlap = set(tactics) & set(pb["apt_tactics"])
                score = len(overlap)

            candidates.append((score, pb))

        if not candidates:
            # Fallback to highest severity match
            for pb in _BUILTIN_PLAYBOOKS:
                if severity.upper() in pb["severity_trigger"]:
                    return pb
            return None

        # Sort by tactic overlap score
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # ── Incident Management ──────────────────────────────────────────────

    def create_incident(
        self,
        alert_data: Dict[str, Any],
        severity: str,
        attribution: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        mode: str = "simulate",
    ) -> Dict[str, Any]:
        """Create a new SOAR incident from alert data."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        # Auto-generate title if not provided
        if not title:
            apt_name = ""
            if attribution and attribution.get("candidate_groups"):
                top = attribution["candidate_groups"][0]
                apt_name = top.get("group_name", "Unknown")
            title = f"Security Incident: {severity} severity"
            if apt_name:
                title += f" (attributed: {apt_name})"

        # Auto-select playbook
        tactics = []
        if attribution:
            observed_ttps = attribution.get("observed_ttps", [])
            # We'd map TTPs to tactics here; for now use alert data
            tactics = alert_data.get("tactics", [])

        playbook = self.select_playbook(severity, tactics)
        playbook_id = playbook["id"] if playbook else ""

        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO soar_incidents
                   (id, created_at, updated_at, title, description, severity, status, attributed_apt, alert_data, playbook_id, mode)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    incident_id, now, now, title,
                    json.dumps(alert_data),
                    severity.upper(), "OPEN",
                    json.dumps(attribution or {}),
                    json.dumps(alert_data),
                    playbook_id, mode,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        # Pre-populate actions from playbook
        if playbook:
            self._populate_actions(incident_id, playbook)

        return {
            "incident_id": incident_id,
            "title": title,
            "severity": severity.upper(),
            "status": "OPEN",
            "playbook_id": playbook_id,
            "playbook_name": playbook["name"] if playbook else "None",
            "mode": mode,
            "action_count": len(playbook["actions"]) if playbook else 0,
            "created_at": now,
        }

    def _populate_actions(self, incident_id: str, playbook: Dict[str, Any]) -> None:
        """Create action log entries from a playbook."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        conn = self._get_connection()
        try:
            for action in playbook["actions"]:
                action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
                conn.execute(
                    """INSERT INTO soar_action_log
                       (id, incident_id, created_at, step_number, action_description, action_type, status, automated)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        action_id, incident_id, now,
                        action["step"], action["action"],
                        action.get("type", ""), "PENDING",
                        1 if action.get("automated") else 0,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def execute_playbook(
        self, incident_id: str, mode: str = "simulate"
    ) -> Dict[str, Any]:
        """Execute (or simulate) all pending playbook actions for an incident."""
        conn = self._get_connection()
        try:
            # Get incident
            incident = conn.execute("SELECT * FROM soar_incidents WHERE id = ?", (incident_id,)).fetchone()
            if not incident:
                return {"error": f"Incident {incident_id} not found"}

            # Get pending actions
            actions = conn.execute(
                "SELECT * FROM soar_action_log WHERE incident_id = ? AND status = 'PENDING' ORDER BY step_number",
                (incident_id,),
            ).fetchall()

            results = []
            now = datetime.datetime.utcnow().isoformat() + "Z"

            for action in actions:
                if mode == "simulate":
                    status = "SIMULATED"
                    result = f"[SIMULATION] Would execute: {action['action_description']}"
                elif mode == "auto_execute" and action["automated"]:
                    status = "COMPLETED"
                    result = f"[AUTO-EXECUTED] {action['action_description']}"
                elif mode == "approve":
                    status = "AWAITING_APPROVAL"
                    result = "Awaiting human approval"
                else:
                    status = "PENDING"
                    result = "Manual action required"

                conn.execute(
                    "UPDATE soar_action_log SET status = ?, result = ? WHERE id = ?",
                    (status, result, action["id"]),
                )
                results.append({
                    "action_id": action["id"],
                    "step": action["step_number"],
                    "description": action["action_description"],
                    "type": action["action_type"],
                    "status": status,
                    "result": result,
                    "automated": bool(action["automated"]),
                })

            # Update incident status
            new_status = "IN_PROGRESS" if mode == "approve" else "RESPONDED"
            conn.execute(
                "UPDATE soar_incidents SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now, incident_id),
            )
            conn.commit()

            return {
                "incident_id": incident_id,
                "mode": mode,
                "actions_processed": len(results),
                "actions": results,
                "incident_status": new_status,
            }
        finally:
            conn.close()

    def get_response_actions(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all actions for an incident."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM soar_action_log WHERE incident_id = ? ORDER BY step_number",
                (incident_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident details."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM soar_incidents WHERE id = ?", (incident_id,)).fetchone()
            if row:
                d = dict(row)
                d["alert_data"] = json.loads(d.get("alert_data") or "{}")
                d["attributed_apt"] = json.loads(d.get("attributed_apt") or "{}")
                return d
        finally:
            conn.close()
        return None

    def get_incidents(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List incidents, optionally filtered by status."""
        conn = self._get_connection()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM soar_incidents WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.upper(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM soar_incidents ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["alert_data"] = json.loads(d.get("alert_data") or "{}")
                d["attributed_apt"] = json.loads(d.get("attributed_apt") or "{}")
                results.append(d)
            return results
        finally:
            conn.close()

    def generate_containment_plan(
        self,
        attributed_apt: Dict[str, Any],
        predictions: Dict[str, Any],
        org_assets: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate an org-specific containment plan combining attribution, predictions, and architecture."""
        now = datetime.datetime.utcnow().isoformat() + "Z"

        # Determine primary threat
        top_group = None
        if attributed_apt.get("candidate_groups"):
            top_group = attributed_apt["candidate_groups"][0]

        group_name = top_group["group_name"] if top_group else "Unknown Threat Actor"
        confidence = top_group["confidence"] if top_group else 0

        # Immediate containment actions
        immediate_actions = [
            {
                "priority": "CRITICAL",
                "action": "Activate Incident Response Team and establish war room",
                "timeframe": "0-15 minutes",
            },
            {
                "priority": "CRITICAL",
                "action": f"Brief team on attributed threat actor: {group_name} (confidence: {confidence:.1%})",
                "timeframe": "0-15 minutes",
            },
        ]

        # Add prediction-based containment
        current_phase = predictions.get("current_phase", {}).get("tactic_name", "Unknown")
        stage = predictions.get("kill_chain_progress", {}).get("estimated_attack_stage", "UNKNOWN")

        if stage == "EARLY":
            immediate_actions.append({
                "priority": "HIGH",
                "action": "Focus on blocking initial access vectors — patch exploited services, block phishing domains",
                "timeframe": "0-1 hour",
            })
        elif stage == "MID":
            immediate_actions.append({
                "priority": "CRITICAL",
                "action": "Isolate compromised segments — block lateral movement via SMB/RDP restrictions",
                "timeframe": "0-30 minutes",
            })
        elif stage == "LATE":
            immediate_actions.append({
                "priority": "CRITICAL",
                "action": "EMERGENCY: Block all outbound traffic from compromised hosts — exfiltration likely in progress",
                "timeframe": "IMMEDIATE",
            })

        # Org-specific actions based on assets
        if org_assets:
            asset_types = set(a.get("asset_type", "") for a in org_assets)
            if "web_server" in asset_types or "application" in asset_types:
                immediate_actions.append({
                    "priority": "HIGH",
                    "action": "Deploy WAF rules and scan web servers for web shells",
                    "timeframe": "1-2 hours",
                })
            if "database" in asset_types:
                immediate_actions.append({
                    "priority": "HIGH",
                    "action": "Audit database access logs and restrict external connections",
                    "timeframe": "1-2 hours",
                })

        # Short-term remediation (24h)
        short_term = [
            {"action": "Complete forensic memory and disk imaging of all affected hosts", "timeframe": "24 hours"},
            {"action": "Rotate all credentials associated with compromised systems", "timeframe": "24 hours"},
            {"action": "Deploy additional monitoring and alerting rules for attributed group's TTPs", "timeframe": "24 hours"},
            {"action": "Submit IOCs to CERT-In and relevant ISACs", "timeframe": "24 hours"},
        ]

        # Long-term hardening (7-30 days)
        long_term = [
            {"action": "Implement network segmentation based on attack path analysis", "timeframe": "7 days"},
            {"action": "Deploy zero-trust architecture for critical assets", "timeframe": "30 days"},
            {"action": "Conduct organisation-wide threat hunting for attributed group's indicators", "timeframe": "7 days"},
            {"action": "Review and update incident response playbooks based on lessons learned", "timeframe": "14 days"},
            {"action": "Conduct tabletop exercise simulating attributed group's attack chain", "timeframe": "30 days"},
        ]

        return {
            "generated_at": now,
            "attributed_group": group_name,
            "attribution_confidence": confidence,
            "current_attack_phase": current_phase,
            "estimated_attack_stage": stage,
            "immediate_containment": immediate_actions,
            "short_term_remediation": short_term,
            "long_term_hardening": long_term,
            "total_actions": len(immediate_actions) + len(short_term) + len(long_term),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return incident summary statistics."""
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) AS c FROM soar_incidents").fetchone()["c"]
            by_status = {}
            for row in conn.execute("SELECT status, COUNT(*) AS c FROM soar_incidents GROUP BY status").fetchall():
                by_status[row["status"]] = row["c"]
            by_severity = {}
            for row in conn.execute("SELECT severity, COUNT(*) AS c FROM soar_incidents GROUP BY severity").fetchall():
                by_severity[row["severity"]] = row["c"]
            return {
                "total_incidents": total,
                "by_status": by_status,
                "by_severity": by_severity,
                "available_playbooks": len(_BUILTIN_PLAYBOOKS),
            }
        finally:
            conn.close()
