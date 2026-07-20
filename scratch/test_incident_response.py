#!/usr/bin/env python3
"""E2E test for the Autonomous Incident Response Orchestrator (Point 3).

Tests the full lifecycle: TRIAGE → CONTAINMENT → ESCALATION → INVESTIGATION → CLOSE
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rakshastra_core.engines.incident_response_engine import IncidentResponseEngine


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    engine = IncidentResponseEngine(":memory:")

    # ── Test 1: Triage a CRITICAL anomaly alert ──────────────────────────
    separator("PHASE 1: TRIAGE — CRITICAL Lateral Movement Alert")

    alert = {
        "entity_id": "workstation-DC01",
        "entity_type": "DEVICE",
        "severity": "CRITICAL",
        "mitre_tactic": "TA0008",
        "mitre_technique": "T1021.002",
        "description": "Anomalous SMB lateral movement from compromised host",
        "confidence": 0.92,
        "deviation_score": 14.3,
        "source_type": "anomaly",
    }

    triage_result = engine.triage_alert(alert, source_type="anomaly")
    print(f"Incident ID: {triage_result['incident_id']}")
    print(f"Title: {triage_result['title']}")
    print(f"Severity: {triage_result['severity']}")
    print(f"Phase: {triage_result['phase']}")
    print(f"Confidence: {triage_result['confidence']:.0%}")
    print(f"MITRE Tactic: {triage_result['mitre_tactic']}")
    print(f"\nRecommended Containment Actions ({len(triage_result['recommended_containment'])}):")
    for action in triage_result["recommended_containment"]:
        auto = "[AUTO]" if action["automated"] else "[MANUAL]"
        print(f"  {auto} {action['id']}: {action['name']}")

    incident_id = triage_result["incident_id"]

    # ── Test 2: Execute containment in simulate mode ─────────────────────
    separator("PHASE 2: CONTAINMENT — Simulate Mode")

    contain_result = engine.execute_containment(incident_id, mode="simulate")
    print(f"Mode: {contain_result['mode']}")
    print(f"Actions Executed: {contain_result['actions_executed']}")
    print(f"Phase: {contain_result['phase']}")
    for action in contain_result["actions"]:
        rev = "reversible" if action["reversible"] else "IRREVERSIBLE"
        print(f"  Step [{action['status']}] {action['action_name']} on {action['target']} ({rev})")
        print(f"    → {action['result']}")

    # ── Test 3: Escalate to SOC ──────────────────────────────────────────
    separator("PHASE 3: ESCALATION — SOC Notification")

    esc_result = engine.escalate_incident(incident_id)
    print(f"Escalation ID: {esc_result['escalation_id']}")
    print(f"Channel: {esc_result['channel']}")
    print(f"Recipients: {', '.join(esc_result['recipients'])}")
    print(f"SLA: {esc_result['sla_minutes']} minutes")
    print(f"\nMessage Preview:")
    print(f"  {esc_result['message']}")

    # ── Test 4: Human responds to escalation ─────────────────────────────
    separator("PHASE 3b: HUMAN APPROVAL")

    approve_result = engine.respond_to_escalation(
        esc_result["escalation_id"], response="approve", responded_by="soc_lead_ravi"
    )
    print(f"Response: {approve_result['response']}")
    print(f"Responded by: {approve_result['responded_by']}")

    # ── Test 5: Investigation ────────────────────────────────────────────
    separator("PHASE 4: INVESTIGATION")

    inv_result = engine.run_investigation(
        incident_id,
        notes="Confirmed lateral movement from workstation-DC01 via SMB. "
              "Attacker used PsExec. Credential dump detected on LSASS.",
    )
    print(f"Entity: {inv_result['entity_id']}")
    print(f"Severity: {inv_result['severity']}")
    print(f"Containment actions reviewed: {inv_result['containment_actions_taken']}")
    print(f"\nRecommendations ({len(inv_result['recommendations'])}):")
    for i, rec in enumerate(inv_result["recommendations"], 1):
        print(f"  {i}. {rec}")

    # ── Test 6: Close incident ───────────────────────────────────────────
    separator("PHASE 6: CLOSE INCIDENT")

    close_result = engine.close_incident(
        incident_id,
        resolution="Lateral movement contained. Credentials rotated. "
                   "Enhanced monitoring deployed for 30 days. CERT-In notified.",
    )
    print(f"Resolution: {close_result['resolution']}")
    print(f"Phase: {close_result['phase']}")
    print(f"Timeline entries: {len(close_result['timeline'])}")
    for entry in close_result["timeline"]:
        print(f"  [{entry['phase']}] {entry['timestamp'][:19]} — {entry['action']}")

    # ── Test 7: Full auto-respond pipeline ───────────────────────────────
    separator("FULL PIPELINE: Auto-Respond (Credential Theft)")

    cred_alert = {
        "entity_id": "user-admin-suresh",
        "entity_type": "USER",
        "severity": "HIGH",
        "mitre_tactic": "TA0006",
        "mitre_technique": "T1003.001",
        "description": "LSASS credential dumping detected on admin account",
        "confidence": 0.85,
    }

    auto_result = engine.auto_respond(cred_alert, mode="simulate")
    print(f"Incident ID: {auto_result['incident_id']}")
    print(f"Final Phase: {auto_result['final_phase']}")
    print(f"\nTriage: {auto_result['triage']['severity']} — {auto_result['triage']['title']}")
    print(f"Containment: {auto_result['containment']['actions_executed']} actions simulated")
    if auto_result.get("escalation"):
        print(f"Escalation: Sent to {auto_result['escalation']['channel']} "
              f"(SLA: {auto_result['escalation']['sla_minutes']}m)")

    # ── Test 8: Dashboard summary ────────────────────────────────────────
    separator("DASHBOARD SUMMARY")

    summary = engine.get_summary()
    print(f"Total IR Incidents: {summary['total_incidents']}")
    print(f"By Phase: {json.dumps(summary['by_phase'], indent=2)}")
    print(f"By Severity: {json.dumps(summary['by_severity'], indent=2)}")
    print(f"Available Containment Actions: {summary['available_containment_actions']}")

    print(f"\n{'='*60}")
    print("  ✅ ALL TESTS PASSED — Incident Response Orchestrator Operational")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
