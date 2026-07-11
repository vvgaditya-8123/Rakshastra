---
name: behavioral-anomaly-detection
description: Behavioral anomaly detection engine for continuous threat monitoring without relying on malware signatures.
version: 1.0.0
author: Rakshastra Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  rakshastra:
    tags: [security, anomaly-detection, behavioral-analytics, cyber-resilience, UEBA]
    related_skills: [incident-response, network-scan, windows-audit, linux-audit]
---

# Behavioural Anomaly Detection Playbook

## Overview
This skill enables the Rakshastra agent to act as a **Behavioural Anomaly Detection Engine** — a continuous monitoring system that builds baseline behavioral profiles for users, devices, and network segments, then detects deviations from those baselines using statistical analysis (z-score deviation). Unlike signature-based detection, this approach catches **zero-day attacks, insider threats, and APT lateral movement** by identifying *how* systems behave abnormally, not *what* malware they match.

## Core Principles
- **No signatures required**: Detection is based purely on behavioral deviation.
- **Continuous learning**: Baselines update incrementally with every new observation using Welford's algorithm.
- **MITRE ATT&CK mapped**: Every anomaly is automatically mapped to a MITRE ATT&CK tactic and technique.
- **Human-in-the-loop**: High-severity anomalies generate recommended actions but require human approval for containment.

## Methodology (7-Phase Sequence)

### 1. **Baseline Collection** (Initial Setup)
Run the system telemetry collector multiple times over several days to build reliable baselines:
```
Use behavioral_collect_system with source="all"
```
Repeat this at regular intervals (e.g., every hour via cronjob) for at least 5 cycles to establish a statistically meaningful baseline. The engine needs a minimum of 5 observations per entity/feature before it starts scoring anomalies.

### 2. **Continuous Monitoring**
Once baselines are established, schedule periodic collection:
- **Login events**: Collect every 15 minutes to detect unusual login hours and locations.
- **Process counts**: Collect every 30 minutes to detect process injection or spawning anomalies.
- **Network connections**: Collect every 15 minutes to detect beaconing or lateral movement.

Use the `cronjob` tool to schedule `behavioral_collect_system` runs.

### 3. **Anomaly Detection & Triage**
When anomalies are detected, the engine automatically:
- Computes a **deviation score** (z-score) indicating how far the observation is from normal.
- Assigns a **severity** (LOW/MEDIUM/HIGH/CRITICAL) based on the z-score magnitude.
- Maps the anomaly to a **MITRE ATT&CK tactic** and **technique**.
- Generates a **recommended action** (e.g., "Force MFA re-authentication", "Block source IP").

Query anomalies:
```
Use behavioral_query_anomalies with severity="HIGH" or category="LOGIN_TIME"
```

### 4. **Investigation**
For each HIGH or CRITICAL anomaly, the agent should:
1. Cross-reference with other anomaly categories for the same entity (correlation).
2. Check the entity's full baseline profile to understand what "normal" looks like.
3. Use `security_scan` to perform targeted scans on the affected host.
4. Use `security_evidence` to formally record findings.

### 5. **Escalation**
If the anomaly correlates with other suspicious signals:
- Use the messaging gateway (Telegram/Discord/Slack/WhatsApp) to alert the security team.
- Include: entity ID, anomaly category, deviation score, MITRE mapping, and recommended action.
- Wait for human approval before executing containment actions.

### 6. **Dashboard Review**
Periodically review the aggregate anomaly summary:
```
Use behavioral_anomaly_summary
```
This provides counts by severity, category, and top anomalous entities — useful for weekly security posture reports.

### 7. **Baseline Recalibration**
If the operational environment changes (e.g., new shift schedules, infrastructure migration):
```
Use behavioral_rebuild_baseline with entity_id="<entity>" and feature_name="<feature>"
```
This recalculates the baseline from all stored historical observations.

## Feature Dimensions Tracked
| Feature Name | Entity Type | What It Measures |
|---|---|---|
| `login_hour` | USER | Hour of day when the user logs in |
| `process_count` | DEVICE | Total number of running processes |
| `active_connections` | DEVICE | Number of established TCP connections |
| `bytes_out_per_hour` | DEVICE | Outbound network traffic volume |
| `file_access_count` | USER | Number of files accessed in a period |
| `command_count` | USER | Number of commands executed in a session |
| `rdp_session_count` | DEVICE | Active Remote Desktop sessions |

## Commands Reference
The agent uses these tools via function calling (not terminal commands):
- `behavioral_collect_system` — Collect real system telemetry and ingest it.
- `behavioral_ingest` — Manually ingest a single observation.
- `behavioral_query_anomalies` — Query detected anomalies with filters.
- `behavioral_get_baselines` — View stored baselines.
- `behavioral_anomaly_summary` — Get aggregate dashboard summary.
- `behavioral_rebuild_baseline` — Recalibrate a baseline from history.
