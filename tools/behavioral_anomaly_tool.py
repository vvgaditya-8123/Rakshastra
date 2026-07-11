#!/usr/bin/env python3
"""Behavioural Anomaly Detection Tools.

Registers agent-callable tools for:
  - Ingesting system observations (login events, process events, network flows)
  - Querying detected anomalies
  - Viewing behavioral baselines
  - Getting anomaly summary dashboards
  - Rebuilding baselines from historical data

These tools form the core of Point 1 (Behavioural Anomaly Detection Engine)
in the Rakshastra Cyber Resilience platform. The agent uses these tools to
monitor infrastructure, detect deviations from normal behavior, and trigger
investigation workflows — all without relying on malware signatures.
"""

import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from rakshastra_constants import get_rakshastra_home
from tools.registry import registry, tool_error, tool_result

# Lazy singleton for the engine
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rakshastra_core.engines.behavioral_analytics import BehavioralAnalyticsEngine
        db_path = get_rakshastra_home() / "behavioral_analytics.db"
        _engine = BehavioralAnalyticsEngine(db_path)
    return _engine


def check_behavioral_anomaly_requirements() -> bool:
    """Always available — no external dependencies required."""
    return True


# =============================================================================
# System Log Collectors (Windows + Linux)
# =============================================================================

def _collect_windows_login_events() -> list:
    """Collect recent Windows Security login events via PowerShell."""
    observations = []
    try:
        ps_cmd = (
            "Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} "
            "-MaxEvents 50 -ErrorAction SilentlyContinue | "
            "Select-Object TimeCreated, "
            "@{N='User';E={$_.Properties[5].Value}}, "
            "@{N='LogonType';E={$_.Properties[8].Value}}, "
            "@{N='SourceIP';E={$_.Properties[18].Value}} | "
            "ConvertTo-Json"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            events = json.loads(result.stdout)
            if isinstance(events, dict):
                events = [events]
            for evt in events:
                time_str = evt.get("TimeCreated", "")
                user = evt.get("User", "UNKNOWN")
                # Extract hour from the timestamp for login_hour feature
                try:
                    if "/Date(" in str(time_str):
                        # PowerShell /Date(timestamp)/ format
                        ts = int(str(time_str).split("(")[1].split(")")[0]) // 1000
                        hour = datetime.fromtimestamp(ts).hour
                    else:
                        hour = datetime.fromisoformat(str(time_str)).hour
                except Exception:
                    hour = datetime.utcnow().hour

                observations.append({
                    "entity_id": user,
                    "entity_type": "USER",
                    "feature_name": "login_hour",
                    "value": float(hour),
                    "raw_data": {
                        "source": "windows_security_log",
                        "event_id": 4624,
                        "logon_type": evt.get("LogonType", ""),
                        "source_ip": evt.get("SourceIP", ""),
                    },
                })
    except Exception:
        pass
    return observations


def _collect_windows_process_events() -> list:
    """Collect current running processes on Windows for process count baseline."""
    observations = []
    try:
        ps_cmd = (
            "Get-Process | Group-Object -Property ProcessName | "
            "Select-Object Name, Count | ConvertTo-Json"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            groups = json.loads(result.stdout)
            if isinstance(groups, dict):
                groups = [groups]
            total_processes = sum(g.get("Count", 0) for g in groups)
            observations.append({
                "entity_id": platform.node(),
                "entity_type": "DEVICE",
                "feature_name": "process_count",
                "value": float(total_processes),
                "raw_data": {"source": "windows_tasklist", "unique_names": len(groups)},
            })
    except Exception:
        pass
    return observations


def _collect_windows_network_connections() -> list:
    """Collect active network connection count on Windows."""
    observations = []
    try:
        ps_cmd = (
            "Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | "
            "Measure-Object | Select-Object -ExpandProperty Count"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            count = int(result.stdout.strip())
            observations.append({
                "entity_id": platform.node(),
                "entity_type": "DEVICE",
                "feature_name": "active_connections",
                "value": float(count),
                "raw_data": {"source": "windows_netstat"},
            })
    except Exception:
        pass
    return observations


def _collect_linux_login_events() -> list:
    """Collect recent Linux auth.log login events."""
    observations = []
    auth_log = Path("/var/log/auth.log")
    if not auth_log.exists():
        auth_log = Path("/var/log/secure")
    if not auth_log.exists():
        return observations

    try:
        result = subprocess.run(
            ["grep", "session opened", str(auth_log)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()[-50:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        time_part = parts[2]
                        hour = int(time_part.split(":")[0])
                    except (ValueError, IndexError):
                        hour = 0
                    user = "unknown"
                    for i, part in enumerate(parts):
                        if part == "user" and i + 1 < len(parts):
                            user = parts[i + 1]
                            break
                    observations.append({
                        "entity_id": user,
                        "entity_type": "USER",
                        "feature_name": "login_hour",
                        "value": float(hour),
                        "raw_data": {"source": "auth.log", "raw_line": line[:200]},
                    })
    except Exception:
        pass
    return observations


# =============================================================================
# Tool Handlers
# =============================================================================

def behavioral_ingest_handler(args: Dict[str, Any], **kwargs) -> str:
    """Ingest a single observation and check for anomalies."""
    entity_id = args.get("entity_id", "")
    entity_type = args.get("entity_type", "USER")
    feature_name = args.get("feature_name", "")
    value = args.get("value", 0.0)
    raw_data = args.get("raw_data", {})

    if not entity_id or not feature_name:
        return tool_error("entity_id and feature_name are required")

    try:
        engine = _get_engine()
        anomaly = engine.ingest_observation(
            entity_id=entity_id,
            entity_type=entity_type,
            feature_name=feature_name,
            value=float(value),
            raw_data=raw_data,
        )
        if anomaly:
            return tool_result(
                success=True,
                anomaly_detected=True,
                anomaly=anomaly.to_dict(),
                message=f"ANOMALY DETECTED: {anomaly.description}",
            )
        return tool_result(
            success=True,
            anomaly_detected=False,
            message=f"Observation ingested for {entity_id}/{feature_name}. No anomaly detected.",
        )
    except Exception as e:
        return tool_error(f"Ingestion failed: {e}")


def behavioral_collect_system_handler(args: Dict[str, Any], **kwargs) -> str:
    """Collect real system telemetry (logins, processes, network) and ingest it."""
    source = args.get("source", "all").lower()

    try:
        engine = _get_engine()
        observations = []

        if os.name == "nt":
            # Windows
            if source in ("all", "logins"):
                observations.extend(_collect_windows_login_events())
            if source in ("all", "processes"):
                observations.extend(_collect_windows_process_events())
            if source in ("all", "network"):
                observations.extend(_collect_windows_network_connections())
        else:
            # Linux/macOS
            if source in ("all", "logins"):
                observations.extend(_collect_linux_login_events())

        if not observations:
            return tool_result(
                success=True,
                observations_count=0,
                anomalies_count=0,
                message="No system observations could be collected. "
                        "This may require elevated privileges (Run as Administrator on Windows).",
            )

        anomalies = engine.ingest_batch(observations)
        anomaly_dicts = [a.to_dict() for a in anomalies]

        return tool_result(
            success=True,
            observations_count=len(observations),
            anomalies_count=len(anomalies),
            anomalies=anomaly_dicts,
            message=f"Collected {len(observations)} observations. "
                    f"Detected {len(anomalies)} anomalies.",
        )
    except Exception as e:
        return tool_error(f"System collection failed: {e}")


def behavioral_query_anomalies_handler(args: Dict[str, Any], **kwargs) -> str:
    """Query stored anomaly events with optional filters."""
    entity_id = args.get("entity_id")
    severity = args.get("severity")
    category = args.get("category")
    since = args.get("since")
    limit = args.get("limit", 50)

    try:
        engine = _get_engine()
        anomalies = engine.get_anomalies(
            entity_id=entity_id,
            severity=severity,
            category=category,
            since=since,
            limit=limit,
        )
        return tool_result(
            success=True,
            count=len(anomalies),
            anomalies=anomalies,
        )
    except Exception as e:
        return tool_error(f"Query failed: {e}")


def behavioral_get_baselines_handler(args: Dict[str, Any], **kwargs) -> str:
    """View behavioral baselines for entities."""
    entity_id = args.get("entity_id")

    try:
        engine = _get_engine()
        baselines = engine.get_baselines(entity_id=entity_id)
        return tool_result(
            success=True,
            count=len(baselines),
            baselines=baselines,
        )
    except Exception as e:
        return tool_error(f"Baseline query failed: {e}")


def behavioral_summary_handler(args: Dict[str, Any], **kwargs) -> str:
    """Get an aggregate anomaly summary for dashboard reporting."""
    try:
        engine = _get_engine()
        summary = engine.get_anomaly_summary()
        return tool_result(success=True, **summary)
    except Exception as e:
        return tool_error(f"Summary failed: {e}")


def behavioral_rebuild_baseline_handler(args: Dict[str, Any], **kwargs) -> str:
    """Rebuild a baseline from all stored historical observations."""
    entity_id = args.get("entity_id", "")
    feature_name = args.get("feature_name", "")

    if not entity_id or not feature_name:
        return tool_error("entity_id and feature_name are required")

    try:
        engine = _get_engine()
        baseline = engine.build_baseline_from_history(entity_id, feature_name)
        if baseline:
            return tool_result(
                success=True,
                baseline=baseline.to_dict(),
                message=f"Baseline rebuilt for {entity_id}/{feature_name} from {baseline.sample_count} observations.",
            )
        return tool_result(
            success=False,
            message=f"No historical observations found for {entity_id}/{feature_name}.",
        )
    except Exception as e:
        return tool_error(f"Baseline rebuild failed: {e}")


# =============================================================================
# OpenAI Function-Calling Schemas
# =============================================================================

BEHAVIORAL_INGEST_SCHEMA = {
    "name": "behavioral_ingest",
    "description": (
        "Ingest a single behavioral observation (login event, process event, "
        "network flow) into the anomaly detection engine. The engine scores it "
        "against the stored baseline and returns an anomaly if deviation is significant. "
        "No malware signatures are used — detection is purely behavioral."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "Unique identifier for the entity (username, hostname, IP, subnet).",
            },
            "entity_type": {
                "type": "string",
                "enum": ["USER", "DEVICE", "NETWORK_SEGMENT", "PROCESS", "SERVICE"],
                "description": "Type of entity being observed.",
            },
            "feature_name": {
                "type": "string",
                "description": (
                    "The behavioral feature being measured. Examples: "
                    "'login_hour', 'process_count', 'bytes_out_per_hour', "
                    "'active_connections', 'file_access_count', 'command_count'."
                ),
            },
            "value": {
                "type": "number",
                "description": "The numeric value of the observation.",
            },
            "raw_data": {
                "type": "object",
                "description": "Optional raw context data (source log, event details).",
            },
        },
        "required": ["entity_id", "entity_type", "feature_name", "value"],
    },
}

BEHAVIORAL_COLLECT_SYSTEM_SCHEMA = {
    "name": "behavioral_collect_system",
    "description": (
        "Automatically collect real system telemetry from the current machine — "
        "login events (Windows Security Log / Linux auth.log), running process counts, "
        "and active network connection counts. Ingests all collected observations "
        "into the behavioral engine and reports any detected anomalies. "
        "Run this periodically to build baselines and detect deviations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["all", "logins", "processes", "network"],
                "description": "Which telemetry sources to collect. Default: all.",
            },
        },
        "required": [],
    },
}

BEHAVIORAL_QUERY_ANOMALIES_SCHEMA = {
    "name": "behavioral_query_anomalies",
    "description": (
        "Query stored behavioral anomaly events. Filter by entity, severity, "
        "category, or time range. Returns a list of detected anomalies with "
        "MITRE ATT&CK mappings and recommended actions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "Filter by entity ID (user, device, etc.).",
            },
            "severity": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
                "description": "Filter by severity level.",
            },
            "category": {
                "type": "string",
                "enum": [
                    "LOGIN_TIME", "LOGIN_LOCATION", "PRIVILEGE_ESCALATION",
                    "LATERAL_MOVEMENT", "DATA_EXFILTRATION", "PROCESS_ANOMALY",
                    "RESOURCE_ACCESS", "NETWORK_ANOMALY", "PERSISTENCE",
                    "COMMAND_ANOMALY",
                ],
                "description": "Filter by anomaly category.",
            },
            "since": {
                "type": "string",
                "description": "ISO-8601 timestamp to filter anomalies since.",
            },
            "limit": {
                "type": "integer",
                "description": "Max number of results. Default: 50.",
            },
        },
        "required": [],
    },
}

BEHAVIORAL_GET_BASELINES_SCHEMA = {
    "name": "behavioral_get_baselines",
    "description": (
        "View the stored behavioral baselines (normal profiles) for entities. "
        "Shows mean, standard deviation, min/max, and sample count for each "
        "feature dimension. Useful for understanding what 'normal' looks like."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "Filter baselines by entity ID. Omit to see all.",
            },
        },
        "required": [],
    },
}

BEHAVIORAL_SUMMARY_SCHEMA = {
    "name": "behavioral_anomaly_summary",
    "description": (
        "Get an aggregate dashboard summary of all behavioral anomalies — "
        "counts by severity, category, and top anomalous entities. "
        "Also shows total baselines and observations tracked."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

BEHAVIORAL_REBUILD_BASELINE_SCHEMA = {
    "name": "behavioral_rebuild_baseline",
    "description": (
        "Rebuild a behavioral baseline from all stored historical observations "
        "for a specific entity and feature. Useful after cleaning bad data or "
        "when the incremental baseline needs recalibration."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "The entity to rebuild the baseline for.",
            },
            "feature_name": {
                "type": "string",
                "description": "The feature dimension to rebuild.",
            },
        },
        "required": ["entity_id", "feature_name"],
    },
}


# =============================================================================
# Register Tools
# =============================================================================

registry.register(
    name="behavioral_ingest",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_INGEST_SCHEMA,
    handler=behavioral_ingest_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="🧠",
)

registry.register(
    name="behavioral_collect_system",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_COLLECT_SYSTEM_SCHEMA,
    handler=behavioral_collect_system_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="📡",
)

registry.register(
    name="behavioral_query_anomalies",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_QUERY_ANOMALIES_SCHEMA,
    handler=behavioral_query_anomalies_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="🔔",
)

registry.register(
    name="behavioral_get_baselines",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_GET_BASELINES_SCHEMA,
    handler=behavioral_get_baselines_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="📊",
)

registry.register(
    name="behavioral_anomaly_summary",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_SUMMARY_SCHEMA,
    handler=behavioral_summary_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="📈",
)

registry.register(
    name="behavioral_rebuild_baseline",
    toolset="behavioral_anomaly",
    schema=BEHAVIORAL_REBUILD_BASELINE_SCHEMA,
    handler=behavioral_rebuild_baseline_handler,
    check_fn=check_behavioral_anomaly_requirements,
    emoji="🔄",
)
