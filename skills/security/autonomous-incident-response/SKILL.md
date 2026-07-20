---
name: autonomous-incident-response
description: Autonomous incident response orchestrator with human-in-the-loop escalation for containment, investigation, and recovery.
version: 1.0.0
author: Rakshastra Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  rakshastra:
    tags: [security, incident-response, containment, SOAR, escalation, cyber-resilience]
    related_skills: [behavioral-anomaly-detection, threat-intelligence, apt-attribution]
---

# Autonomous Incident Response Playbook

## Overview
This skill enables the Rakshastra agent to act as an **Autonomous Incident Response Orchestrator** — a system that automatically triages security alerts, executes containment actions, escalates to human SOC analysts via messaging gateways, and compiles investigation reports. It bridges the gap between anomaly detection (Point 1) and APT attribution (Point 2) by providing the **action layer** that responds to threats in real time.

## Response Lifecycle (6 Phases)

```
TRIAGE → CONTAINMENT → ESCALATION → INVESTIGATION → RECOVERY → CLOSED
```

### Phase 1: Triage
When a behavioral anomaly or security alert fires, triage it immediately:
```
Use ir_triage_alert with alert_data containing:
  entity_id, entity_type, severity, mitre_tactic, description, confidence
```
This creates an IR incident, scores severity, and recommends containment actions.

### Phase 2: Containment
Execute recommended containment actions. **Always simulate first:**
```
Use ir_execute_containment with incident_id and mode="simulate"
```
Review simulation results. If appropriate, re-run with mode="execute" for real containment, or mode="approve" to queue for human approval.

**Available Containment Actions:**
| Action | ID | Automated | Reversible |
|---|---|---|---|
| Isolate Endpoint | CA-ISOLATE-HOST | ✅ | ✅ |
| Revoke Credential | CA-REVOKE-CRED | ✅ | ✅ |
| Block IP Address | CA-BLOCK-IP | ✅ | ✅ |
| Kill Process | CA-KILL-PROCESS | ✅ | ❌ |
| Disable Service | CA-DISABLE-SERVICE | ❌ | ✅ |
| Quarantine File | CA-QUARANTINE-FILE | ✅ | ✅ |

### Phase 3: Escalation (Human-in-the-Loop)
For CRITICAL and HIGH severity incidents, escalate to the SOC team:
```
Use ir_escalate_incident with incident_id
```
This sends a formatted alert via the messaging gateway (Telegram, Discord, Slack, etc.) with:
- Incident details and MITRE ATT&CK mapping
- Containment status summary
- SLA timer (15 min for CRITICAL, 1 hour for HIGH)
- Instructions for the analyst to respond with /approve or /reject

**Do NOT execute destructive containment (mode="execute") on CRITICAL incidents without human approval.** The escalation gate ensures a human reviews the response before irreversible actions are taken.

### Phase 4: Investigation
After containment and escalation, compile the investigation:
```
Use ir_investigate with incident_id and optional analyst notes
```
This correlates all containment results, escalation responses, and alert data into a structured report with remediation recommendations.

### Phase 5: Recovery
Recovery actions depend on the incident type:
- **Credential compromise**: Rotate credentials, re-enable MFA, monitor for 30 days
- **Ransomware**: Verify backups, re-image hosts, deploy enhanced EDR
- **Lateral movement**: Re-segment network, deploy honeypots
- **Data exfiltration**: Notify DPO, assess DPDPA/GDPR obligations

### Phase 6: Close
Close the incident with a resolution summary:
```
Use ir_close_incident with incident_id and resolution description
```

## Quick Auto-Response (Single Command)
For hands-free response to an alert, use the full pipeline:
```
Use ir_auto_respond with alert_data and mode="simulate"
```
This runs triage → containment → escalation in one call. Use mode="execute" only after reviewing simulate results.

## Integration with Point 1 & 2
- **From Behavioral Anomaly Detection**: When `behavioral_collect_system` detects a CRITICAL anomaly, pipe the anomaly data directly into `ir_auto_respond`.
- **From APT Attribution**: When `apt_full_analysis` identifies a threat actor, use the attribution data to enrich the `ir_triage_alert` call with MITRE tactics.
- **SOAR Playbooks**: The IR engine works alongside the existing SOAR playbooks (PB-001 through PB-006) — use SOAR for broad playbook orchestration and IR for targeted containment.

## Commands Reference
- `ir_triage_alert` — Triage an alert and create an IR incident
- `ir_execute_containment` — Execute containment (simulate/execute/approve)
- `ir_escalate_incident` — Escalate to SOC via messaging gateway
- `ir_investigate` — Compile investigation report
- `ir_auto_respond` — Full pipeline in one call
- `ir_close_incident` — Close with resolution
- `ir_dashboard_summary` — Aggregate IR dashboard
