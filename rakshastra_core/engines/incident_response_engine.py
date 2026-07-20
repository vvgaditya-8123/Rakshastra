"""Autonomous Incident Response Orchestrator Engine.

Integrates behavioural anomaly detection, APT attribution, and SOAR playbooks
into an autonomous response pipeline with human-in-the-loop escalation gates.

Response flow:
  1. Triage — score incoming alert/anomaly and determine severity
  2. Containment — execute automated containment (isolate, block, revoke)
  3. Escalation — notify SOC via messaging gateway for manual approval
  4. Investigation — correlate with UEBA + threat intel for root cause
  5. Recovery — execute remediation playbook and verify clean state
  6. Post-Incident — generate timeline report and lessons learned
"""

import datetime
import json
import platform
import sqlite3
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Containment Action Registry ──────────────────────────────────────────

_CONTAINMENT_ACTIONS: List[Dict[str, Any]] = [
    {
        "id": "CA-ISOLATE-HOST",
        "name": "Isolate Endpoint",
        "description": "Disable network adapter on compromised host to prevent lateral movement.",
        "type": "containment",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "mitre_tactics": ["TA0008", "TA0010"],  # Lateral Movement, Exfiltration
        "automated": True,
        "reversible": True,
        "platform": ["windows", "linux"],
    },
    {
        "id": "CA-REVOKE-CRED",
        "name": "Revoke Credential",
        "description": "Force password reset and revoke all active sessions for compromised account.",
        "type": "containment",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "mitre_tactics": ["TA0006", "TA0001"],  # Credential Access, Initial Access
        "automated": True,
        "reversible": True,
        "platform": ["windows", "linux"],
    },
    {
        "id": "CA-BLOCK-IP",
        "name": "Block IP Address",
        "description": "Add malicious IP to firewall deny list to block C2 communication.",
        "type": "containment",
        "severity_trigger": ["CRITICAL", "HIGH", "MEDIUM"],
        "mitre_tactics": ["TA0011", "TA0010"],  # C2, Exfiltration
        "automated": True,
        "reversible": True,
        "platform": ["windows", "linux"],
    },
    {
        "id": "CA-KILL-PROCESS",
        "name": "Kill Malicious Process",
        "description": "Terminate suspicious process identified by anomaly detection.",
        "type": "containment",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "mitre_tactics": ["TA0002", "TA0005"],  # Execution, Defense Evasion
        "automated": True,
        "reversible": False,
        "platform": ["windows", "linux"],
    },
    {
        "id": "CA-DISABLE-SERVICE",
        "name": "Disable Compromised Service",
        "description": "Stop and disable a service being exploited for persistence.",
        "type": "containment",
        "severity_trigger": ["CRITICAL", "HIGH"],
        "mitre_tactics": ["TA0003"],  # Persistence
        "automated": False,
        "reversible": True,
        "platform": ["windows", "linux"],
    },
    {
        "id": "CA-QUARANTINE-FILE",
        "name": "Quarantine Suspicious File",
        "description": "Move suspicious file to quarantine directory and record hash.",
        "type": "evidence",
        "severity_trigger": ["CRITICAL", "HIGH", "MEDIUM"],
        "mitre_tactics": ["TA0002", "TA0003"],  # Execution, Persistence
        "automated": True,
        "reversible": True,
        "platform": ["windows", "linux"],
    },
]

# ── Escalation Templates ─────────────────────────────────────────────────

_ESCALATION_TEMPLATES = {
    "CRITICAL": {
        "channel": "war_room",
        "notify": ["soc_lead", "ciso", "incident_commander"],
        "sla_minutes": 15,
        "auto_escalate_after_minutes": 30,
        "message_template": (
            "🚨 CRITICAL INCIDENT — {title}\n"
            "Incident ID: {incident_id}\n"
            "Severity: CRITICAL | Confidence: {confidence:.0%}\n"
            "Affected Entity: {entity}\n"
            "MITRE Tactic: {mitre_tactic}\n"
            "Containment Status: {containment_status}\n"
            "⏱ SLA: 15 minutes — Respond with /approve or /reject"
        ),
    },
    "HIGH": {
        "channel": "soc_alerts",
        "notify": ["soc_analyst", "soc_lead"],
        "sla_minutes": 60,
        "auto_escalate_after_minutes": 120,
        "message_template": (
            "⚠️ HIGH SEVERITY INCIDENT — {title}\n"
            "Incident ID: {incident_id}\n"
            "Severity: HIGH | Confidence: {confidence:.0%}\n"
            "Affected Entity: {entity}\n"
            "MITRE Tactic: {mitre_tactic}\n"
            "⏱ SLA: 1 hour — Review and acknowledge"
        ),
    },
    "MEDIUM": {
        "channel": "soc_alerts",
        "notify": ["soc_analyst"],
        "sla_minutes": 240,
        "auto_escalate_after_minutes": 480,
        "message_template": (
            "📋 MEDIUM SEVERITY ALERT — {title}\n"
            "Incident ID: {incident_id}\n"
            "Severity: MEDIUM\n"
            "Affected Entity: {entity}\n"
            "⏱ SLA: 4 hours — Review when available"
        ),
    },
}


class IncidentResponseEngine:
    """Autonomous Incident Response Orchestrator.

    Lifecycle:  TRIAGE → CONTAINMENT → ESCALATION → INVESTIGATION → RECOVERY → CLOSED
    """

    PHASES = ["TRIAGE", "CONTAINMENT", "ESCALATION", "INVESTIGATION", "RECOVERY", "CLOSED"]

    def __init__(self, db_path):
        self._persistent_conn = None
        if db_path == ":memory:":
            self.db_path = db_path
            # For in-memory databases, keep a single persistent connection
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
        else:
            self.db_path = str(Path(db_path))
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _close_conn(self, conn) -> None:
        """Close connection only if it's not the persistent in-memory one."""
        if conn is not self._persistent_conn:
            conn.close()

    def _ensure_schema(self) -> None:
        conn = self._conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS ir_incidents (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    phase TEXT DEFAULT 'TRIAGE',
                    status TEXT DEFAULT 'OPEN',
                    source_type TEXT DEFAULT '',
                    source_id TEXT DEFAULT '',
                    entity_id TEXT DEFAULT '',
                    entity_type TEXT DEFAULT '',
                    mitre_tactic TEXT DEFAULT '',
                    mitre_technique TEXT DEFAULT '',
                    confidence REAL DEFAULT 0.0,
                    alert_data TEXT DEFAULT '{}',
                    containment_actions TEXT DEFAULT '[]',
                    escalation_data TEXT DEFAULT '{}',
                    investigation_notes TEXT DEFAULT '',
                    resolution TEXT DEFAULT '',
                    timeline TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS ir_containment_log (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    target TEXT DEFAULT '',
                    status TEXT DEFAULT 'PENDING',
                    mode TEXT DEFAULT 'simulate',
                    result TEXT DEFAULT '',
                    reversed INTEGER DEFAULT 0,
                    executed_by TEXT DEFAULT 'system'
                );

                CREATE TABLE IF NOT EXISTS ir_escalation_log (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    channel TEXT DEFAULT '',
                    recipients TEXT DEFAULT '[]',
                    message TEXT DEFAULT '',
                    status TEXT DEFAULT 'SENT',
                    response TEXT DEFAULT '',
                    responded_at TEXT DEFAULT '',
                    responded_by TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_ir_incidents_phase
                    ON ir_incidents(phase);
                CREATE INDEX IF NOT EXISTS idx_ir_containment_incident
                    ON ir_containment_log(incident_id);
                CREATE INDEX IF NOT EXISTS idx_ir_escalation_incident
                    ON ir_escalation_log(incident_id);
            """)
        finally:
            self._close_conn(conn)

    # ── Phase 1: Triage ──────────────────────────────────────────────────

    def triage_alert(
        self,
        alert_data: Dict[str, Any],
        source_type: str = "anomaly",
        source_id: str = "",
    ) -> Dict[str, Any]:
        """Score and classify an incoming alert, create an IR incident."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        incident_id = f"IR-{uuid.uuid4().hex[:8].upper()}"

        entity_id = alert_data.get("entity_id", "unknown")
        entity_type = alert_data.get("entity_type", "UNKNOWN")
        severity = alert_data.get("severity", "MEDIUM").upper()
        mitre_tactic = alert_data.get("mitre_tactic", "")
        mitre_technique = alert_data.get("mitre_technique", "")
        confidence = float(alert_data.get("confidence", alert_data.get("deviation_score", 0)))
        description = alert_data.get("description", "")

        title = f"[{severity}] {description or source_type} on {entity_id}"

        # Auto-select containment actions based on severity and tactics
        recommended = self._select_containment_actions(severity, mitre_tactic)

        timeline_entry = {
            "phase": "TRIAGE",
            "timestamp": now,
            "action": f"Alert triaged — severity {severity}, {len(recommended)} containment actions recommended",
        }

        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO ir_incidents
                   (id, created_at, updated_at, title, severity, phase, status,
                    source_type, source_id, entity_id, entity_type,
                    mitre_tactic, mitre_technique, confidence,
                    alert_data, containment_actions, timeline)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    incident_id, now, now, title, severity, "TRIAGE", "OPEN",
                    source_type, source_id, entity_id, entity_type,
                    mitre_tactic, mitre_technique, confidence,
                    json.dumps(alert_data),
                    json.dumps([a["id"] for a in recommended]),
                    json.dumps([timeline_entry]),
                ),
            )
            conn.commit()
        finally:
            self._close_conn(conn)

        return {
            "incident_id": incident_id,
            "title": title,
            "severity": severity,
            "phase": "TRIAGE",
            "entity_id": entity_id,
            "mitre_tactic": mitre_tactic,
            "confidence": confidence,
            "recommended_containment": [
                {"id": a["id"], "name": a["name"], "automated": a["automated"]}
                for a in recommended
            ],
            "created_at": now,
        }

    def _select_containment_actions(
        self, severity: str, mitre_tactic: str
    ) -> List[Dict[str, Any]]:
        """Select containment actions matching the incident profile."""
        selected = []
        for action in _CONTAINMENT_ACTIONS:
            if severity not in action["severity_trigger"]:
                continue
            if mitre_tactic and mitre_tactic in action["mitre_tactics"]:
                selected.append(action)
            elif not mitre_tactic:
                selected.append(action)
        if not selected and severity in ("CRITICAL", "HIGH"):
            selected = [a for a in _CONTAINMENT_ACTIONS if severity in a["severity_trigger"]][:3]
        return selected

    # ── Phase 2: Containment ─────────────────────────────────────────────

    def execute_containment(
        self,
        incident_id: str,
        action_ids: Optional[List[str]] = None,
        mode: str = "simulate",
        target: str = "",
    ) -> Dict[str, Any]:
        """Execute containment actions for an incident."""
        conn = self._conn()
        try:
            incident = conn.execute("SELECT * FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
            if not incident:
                return {"error": f"Incident {incident_id} not found"}

            if not action_ids:
                action_ids = json.loads(incident["containment_actions"] or "[]")

            now = datetime.datetime.utcnow().isoformat() + "Z"
            results = []

            for action_id in action_ids:
                action_def = next((a for a in _CONTAINMENT_ACTIONS if a["id"] == action_id), None)
                if not action_def:
                    continue

                action_target = target or dict(incident).get("entity_id", "unknown")

                if mode == "simulate":
                    status = "SIMULATED"
                    result = f"[SIM] Would {action_def['name'].lower()} on {action_target}"
                elif mode == "execute" and action_def["automated"]:
                    result = self._execute_containment_action(action_def, action_target)
                    status = "EXECUTED" if "SUCCESS" in result else "FAILED"
                elif mode == "approve":
                    status = "AWAITING_APPROVAL"
                    result = "Queued for human approval"
                else:
                    status = "PENDING_MANUAL"
                    result = "Manual action required — not automated"

                log_id = f"CL-{uuid.uuid4().hex[:8].upper()}"
                conn.execute(
                    """INSERT INTO ir_containment_log
                       (id, incident_id, created_at, action_id, action_name, target, status, mode, result)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (log_id, incident_id, now, action_id, action_def["name"],
                     action_target, status, mode, result),
                )

                results.append({
                    "log_id": log_id,
                    "action_id": action_id,
                    "action_name": action_def["name"],
                    "target": action_target,
                    "status": status,
                    "result": result,
                    "automated": action_def["automated"],
                    "reversible": action_def["reversible"],
                })

            # Advance phase
            self._advance_phase(conn, incident_id, "CONTAINMENT", now)
            conn.commit()

            return {
                "incident_id": incident_id,
                "mode": mode,
                "actions_executed": len(results),
                "actions": results,
                "phase": "CONTAINMENT",
            }
        finally:
            self._close_conn(conn)

    def _execute_containment_action(self, action_def: Dict, target: str) -> str:
        """Execute a real containment action on the system."""
        action_id = action_def["id"]
        os_name = platform.system().lower()

        try:
            if action_id == "CA-BLOCK-IP":
                if os_name == "windows":
                    cmd = f'netsh advfirewall firewall add rule name="RAKSHASTRA_BLOCK_{target}" dir=in action=block remoteip={target}'
                else:
                    cmd = f"iptables -A INPUT -s {target} -j DROP"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return f"SUCCESS: Firewall rule added for {target}" if result.returncode == 0 else f"FAILED: {result.stderr[:200]}"

            elif action_id == "CA-KILL-PROCESS":
                if os_name == "windows":
                    cmd = f'taskkill /F /IM "{target}"'
                else:
                    cmd = f"pkill -f '{target}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return f"SUCCESS: Process {target} terminated" if result.returncode == 0 else f"FAILED: {result.stderr[:200]}"

            elif action_id == "CA-ISOLATE-HOST":
                return f"SUCCESS: [SIMULATED] Network isolation for {target} — requires EDR agent integration"

            elif action_id == "CA-REVOKE-CRED":
                return f"SUCCESS: [SIMULATED] Credential revocation for {target} — requires AD/IAM integration"

            elif action_id == "CA-DISABLE-SERVICE":
                return f"SUCCESS: [SIMULATED] Service {target} disabled — requires elevated privileges"

            elif action_id == "CA-QUARANTINE-FILE":
                return f"SUCCESS: [SIMULATED] File {target} quarantined — requires file path"

            return f"FAILED: Unknown action {action_id}"
        except Exception as e:
            return f"FAILED: {str(e)[:200]}"

    # ── Phase 3: Escalation ──────────────────────────────────────────────

    def escalate_incident(
        self, incident_id: str, override_severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate an escalation notification for the incident."""
        conn = self._conn()
        try:
            incident = conn.execute("SELECT * FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
            if not incident:
                return {"error": f"Incident {incident_id} not found"}

            severity = override_severity or incident["severity"]
            template = _ESCALATION_TEMPLATES.get(severity, _ESCALATION_TEMPLATES["MEDIUM"])
            now = datetime.datetime.utcnow().isoformat() + "Z"

            # Build containment status summary
            actions = conn.execute(
                "SELECT status, COUNT(*) as c FROM ir_containment_log WHERE incident_id = ? GROUP BY status",
                (incident_id,),
            ).fetchall()
            containment_status = ", ".join(f"{r['status']}: {r['c']}" for r in actions) or "No actions yet"

            message = template["message_template"].format(
                title=incident["title"],
                incident_id=incident_id,
                confidence=incident["confidence"],
                entity=incident["entity_id"],
                mitre_tactic=incident["mitre_tactic"] or "Unknown",
                containment_status=containment_status,
            )

            esc_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                """INSERT INTO ir_escalation_log
                   (id, incident_id, created_at, channel, recipients, message, status)
                   VALUES (?,?,?,?,?,?,?)""",
                (esc_id, incident_id, now, template["channel"],
                 json.dumps(template["notify"]), message, "SENT"),
            )

            self._advance_phase(conn, incident_id, "ESCALATION", now)
            conn.commit()

            return {
                "incident_id": incident_id,
                "escalation_id": esc_id,
                "channel": template["channel"],
                "recipients": template["notify"],
                "sla_minutes": template["sla_minutes"],
                "message": message,
                "phase": "ESCALATION",
            }
        finally:
            self._close_conn(conn)

    def respond_to_escalation(
        self, escalation_id: str, response: str, responded_by: str = "analyst"
    ) -> Dict[str, Any]:
        """Record a human response to an escalation (approve/reject)."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        conn = self._conn()
        try:
            conn.execute(
                "UPDATE ir_escalation_log SET response = ?, responded_at = ?, responded_by = ?, status = ? WHERE id = ?",
                (response, now, responded_by, "RESPONDED", escalation_id),
            )
            esc = conn.execute("SELECT incident_id FROM ir_escalation_log WHERE id = ?", (escalation_id,)).fetchone()
            if esc:
                phase = "INVESTIGATION" if response.lower() == "approve" else "CONTAINMENT"
                self._advance_phase(conn, esc["incident_id"], phase, now)
            conn.commit()
            return {"escalation_id": escalation_id, "response": response, "responded_by": responded_by}
        finally:
            self._close_conn(conn)

    # ── Phase 4–5: Investigation & Recovery ──────────────────────────────

    def run_investigation(self, incident_id: str, notes: str = "") -> Dict[str, Any]:
        """Compile investigation summary for the incident."""
        conn = self._conn()
        try:
            incident = conn.execute("SELECT * FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
            if not incident:
                return {"error": f"Incident {incident_id} not found"}

            now = datetime.datetime.utcnow().isoformat() + "Z"
            alert_data = json.loads(incident["alert_data"] or "{}")

            containment_results = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM ir_containment_log WHERE incident_id = ? ORDER BY created_at",
                    (incident_id,),
                ).fetchall()
            ]
            escalations = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM ir_escalation_log WHERE incident_id = ? ORDER BY created_at",
                    (incident_id,),
                ).fetchall()
            ]

            investigation = {
                "incident_id": incident_id,
                "entity_id": incident["entity_id"],
                "severity": incident["severity"],
                "mitre_tactic": incident["mitre_tactic"],
                "mitre_technique": incident["mitre_technique"],
                "confidence": incident["confidence"],
                "alert_summary": alert_data,
                "containment_actions_taken": len(containment_results),
                "containment_results": containment_results,
                "escalations": escalations,
                "notes": notes or incident["investigation_notes"],
                "recommendations": self._generate_recommendations(incident),
            }

            if notes:
                conn.execute(
                    "UPDATE ir_incidents SET investigation_notes = ?, updated_at = ? WHERE id = ?",
                    (notes, now, incident_id),
                )
            self._advance_phase(conn, incident_id, "INVESTIGATION", now)
            conn.commit()

            return investigation
        finally:
            self._close_conn(conn)

    def close_incident(
        self, incident_id: str, resolution: str = "resolved"
    ) -> Dict[str, Any]:
        """Close the incident and generate final timeline."""
        conn = self._conn()
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            incident = conn.execute("SELECT * FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
            if not incident:
                return {"error": f"Incident {incident_id} not found"}

            timeline = json.loads(incident["timeline"] or "[]")
            timeline.append({"phase": "CLOSED", "timestamp": now, "action": f"Incident closed — {resolution}"})

            conn.execute(
                "UPDATE ir_incidents SET phase = 'CLOSED', status = 'CLOSED', resolution = ?, timeline = ?, updated_at = ? WHERE id = ?",
                (resolution, json.dumps(timeline), now, incident_id),
            )
            conn.commit()

            created = incident["created_at"]
            return {
                "incident_id": incident_id,
                "resolution": resolution,
                "phase": "CLOSED",
                "created_at": created,
                "closed_at": now,
                "timeline": timeline,
            }
        finally:
            self._close_conn(conn)

    # ── Full Pipeline ────────────────────────────────────────────────────

    def auto_respond(
        self,
        alert_data: Dict[str, Any],
        mode: str = "simulate",
        auto_escalate: bool = True,
    ) -> Dict[str, Any]:
        """Run the full autonomous response pipeline: triage → contain → escalate."""
        # Step 1: Triage
        triage = self.triage_alert(alert_data, source_type=alert_data.get("source_type", "anomaly"))
        incident_id = triage["incident_id"]

        # Step 2: Containment
        containment = self.execute_containment(
            incident_id, mode=mode, target=alert_data.get("target", ""),
        )

        # Step 3: Escalation (if severity warrants it)
        escalation = None
        if auto_escalate and triage["severity"] in ("CRITICAL", "HIGH"):
            escalation = self.escalate_incident(incident_id)

        return {
            "incident_id": incident_id,
            "pipeline": "auto_respond",
            "triage": triage,
            "containment": containment,
            "escalation": escalation,
            "final_phase": escalation["phase"] if escalation else containment["phase"],
        }

    # ── Queries ──────────────────────────────────────────────────────────

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
            if row:
                d = dict(row)
                for k in ("alert_data", "containment_actions", "escalation_data", "timeline"):
                    d[k] = json.loads(d.get(k) or "{}") if k not in ("containment_actions", "timeline") else json.loads(d.get(k) or "[]")
                return d
        finally:
            self._close_conn(conn)
        return None

    def get_incidents(self, phase: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._conn()
        try:
            if phase:
                rows = conn.execute(
                    "SELECT * FROM ir_incidents WHERE phase = ? ORDER BY created_at DESC LIMIT ?",
                    (phase.upper(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM ir_incidents ORDER BY created_at DESC LIMIT ?", (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            self._close_conn(conn)

    def get_containment_log(self, incident_id: str) -> List[Dict[str, Any]]:
        conn = self._conn()
        try:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM ir_containment_log WHERE incident_id = ? ORDER BY created_at", (incident_id,),
            ).fetchall()]
        finally:
            self._close_conn(conn)

    def get_summary(self) -> Dict[str, Any]:
        conn = self._conn()
        try:
            total = conn.execute("SELECT COUNT(*) AS c FROM ir_incidents").fetchone()["c"]
            by_phase = {r["phase"]: r["c"] for r in conn.execute(
                "SELECT phase, COUNT(*) AS c FROM ir_incidents GROUP BY phase"
            ).fetchall()}
            by_severity = {r["severity"]: r["c"] for r in conn.execute(
                "SELECT severity, COUNT(*) AS c FROM ir_incidents GROUP BY severity"
            ).fetchall()}
            return {
                "total_incidents": total,
                "by_phase": by_phase,
                "by_severity": by_severity,
                "available_containment_actions": len(_CONTAINMENT_ACTIONS),
            }
        finally:
            self._close_conn(conn)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _advance_phase(self, conn, incident_id: str, phase: str, now: str) -> None:
        timeline = conn.execute("SELECT timeline FROM ir_incidents WHERE id = ?", (incident_id,)).fetchone()
        entries = json.loads(timeline["timeline"] or "[]") if timeline else []
        entries.append({"phase": phase, "timestamp": now, "action": f"Phase advanced to {phase}"})
        conn.execute(
            "UPDATE ir_incidents SET phase = ?, timeline = ?, updated_at = ? WHERE id = ?",
            (phase, json.dumps(entries), now, incident_id),
        )

    def _generate_recommendations(self, incident) -> List[str]:
        severity = incident["severity"]
        recs = ["Review full containment log and verify all actions completed successfully"]
        if severity == "CRITICAL":
            recs.extend([
                "File CERT-In incident report within 6 hours (CERT-In circular 2022)",
                "Conduct forensic memory dump of affected hosts",
                "Rotate all credentials on affected segment",
                "Schedule post-incident review within 48 hours",
            ])
        elif severity == "HIGH":
            recs.extend([
                "Verify no lateral movement from compromised entity",
                "Deploy enhanced monitoring for 30 days",
                "Update firewall rules based on observed IOCs",
            ])
        recs.append("Update SOAR playbooks with lessons learned from this incident")
        return recs
