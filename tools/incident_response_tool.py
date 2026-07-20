#!/usr/bin/env python3
"""Autonomous Incident Response Tools.

Registers agent-callable tools for the Incident Response Orchestrator:
  - Triage incoming alerts/anomalies
  - Execute containment actions (isolate, block, revoke)
  - Escalate incidents to SOC via messaging gateway
  - Run investigations and compile findings
  - Close incidents with resolution reports
  - Full auto-respond pipeline (triage → contain → escalate)

These tools form Point 3 (Autonomous Incident Response Orchestrator)
in the Rakshastra Cyber Resilience platform.
"""

import json
from typing import Any, Dict

from rakshastra_constants import get_rakshastra_home
from tools.registry import registry, tool_error, tool_result

# Lazy singleton for the engine
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rakshastra_core.engines.incident_response_engine import IncidentResponseEngine
        db_path = get_rakshastra_home() / "incident_response.db"
        _engine = IncidentResponseEngine(db_path)
    return _engine


def check_incident_response_requirements() -> bool:
    """Always available — no external dependencies required."""
    return True


# =============================================================================
# Tool Handlers
# =============================================================================

def ir_triage_handler(args: Dict[str, Any], **kwargs) -> str:
    """Triage an incoming alert and create an IR incident."""
    alert_data = args.get("alert_data", {})
    source_type = args.get("source_type", "anomaly")

    if not alert_data:
        return tool_error("alert_data is required")

    try:
        engine = _get_engine()
        result = engine.triage_alert(alert_data, source_type=source_type)
        return tool_result(
            success=True,
            **result,
            message=f"Incident {result['incident_id']} created — {result['severity']} severity, "
                    f"{len(result['recommended_containment'])} containment actions recommended.",
        )
    except Exception as e:
        return tool_error(f"Triage failed: {e}")


def ir_contain_handler(args: Dict[str, Any], **kwargs) -> str:
    """Execute containment actions on an incident."""
    incident_id = args.get("incident_id", "")
    mode = args.get("mode", "simulate")
    action_ids = args.get("action_ids")
    target = args.get("target", "")

    if not incident_id:
        return tool_error("incident_id is required")

    try:
        engine = _get_engine()
        result = engine.execute_containment(
            incident_id, action_ids=action_ids, mode=mode, target=target,
        )
        if "error" in result:
            return tool_error(result["error"])
        return tool_result(
            success=True,
            **result,
            message=f"Executed {result['actions_executed']} containment actions in {mode} mode.",
        )
    except Exception as e:
        return tool_error(f"Containment failed: {e}")


def ir_escalate_handler(args: Dict[str, Any], **kwargs) -> str:
    """Escalate an incident to the SOC team via messaging."""
    incident_id = args.get("incident_id", "")

    if not incident_id:
        return tool_error("incident_id is required")

    try:
        engine = _get_engine()
        result = engine.escalate_incident(incident_id)
        if "error" in result:
            return tool_error(result["error"])
        return tool_result(
            success=True,
            **result,
            message=f"Escalation sent to {result['channel']} — SLA: {result['sla_minutes']} minutes.",
        )
    except Exception as e:
        return tool_error(f"Escalation failed: {e}")


def ir_investigate_handler(args: Dict[str, Any], **kwargs) -> str:
    """Compile investigation findings for an incident."""
    incident_id = args.get("incident_id", "")
    notes = args.get("notes", "")

    if not incident_id:
        return tool_error("incident_id is required")

    try:
        engine = _get_engine()
        result = engine.run_investigation(incident_id, notes=notes)
        if "error" in result:
            return tool_error(result["error"])
        return tool_result(
            success=True,
            **result,
            message=f"Investigation compiled — {result['containment_actions_taken']} containment actions reviewed, "
                    f"{len(result['recommendations'])} recommendations generated.",
        )
    except Exception as e:
        return tool_error(f"Investigation failed: {e}")


def ir_auto_respond_handler(args: Dict[str, Any], **kwargs) -> str:
    """Full autonomous response pipeline: triage → contain → escalate."""
    alert_data = args.get("alert_data", {})
    mode = args.get("mode", "simulate")

    if not alert_data:
        return tool_error("alert_data is required")

    try:
        engine = _get_engine()
        result = engine.auto_respond(alert_data, mode=mode)
        triage = result["triage"]
        containment = result["containment"]
        escalation = result.get("escalation")

        summary = (
            f"Auto-response complete for {triage['incident_id']}:\n"
            f"  Severity: {triage['severity']}\n"
            f"  Containment: {containment['actions_executed']} actions ({mode})\n"
        )
        if escalation:
            summary += f"  Escalated to: {escalation['channel']} (SLA: {escalation['sla_minutes']}m)\n"

        return tool_result(success=True, **result, message=summary)
    except Exception as e:
        return tool_error(f"Auto-respond failed: {e}")


def ir_close_handler(args: Dict[str, Any], **kwargs) -> str:
    """Close an incident with a resolution summary."""
    incident_id = args.get("incident_id", "")
    resolution = args.get("resolution", "resolved")

    if not incident_id:
        return tool_error("incident_id is required")

    try:
        engine = _get_engine()
        result = engine.close_incident(incident_id, resolution=resolution)
        if "error" in result:
            return tool_error(result["error"])
        return tool_result(
            success=True,
            **result,
            message=f"Incident {incident_id} closed — {resolution}. Timeline has {len(result['timeline'])} entries.",
        )
    except Exception as e:
        return tool_error(f"Close failed: {e}")


def ir_summary_handler(args: Dict[str, Any], **kwargs) -> str:
    """Get aggregate incident response dashboard summary."""
    try:
        engine = _get_engine()
        summary = engine.get_summary()
        return tool_result(success=True, **summary)
    except Exception as e:
        return tool_error(f"Summary failed: {e}")


# =============================================================================
# OpenAI Function-Calling Schemas
# =============================================================================

IR_TRIAGE_SCHEMA = {
    "name": "ir_triage_alert",
    "description": (
        "Triage an incoming security alert or anomaly detection event. Creates an "
        "Incident Response case, scores severity, maps to MITRE ATT&CK, and recommends "
        "containment actions. Use this when a behavioral anomaly or security alert needs "
        "to be formally tracked and responded to."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "alert_data": {
                "type": "object",
                "description": (
                    "Alert details including: entity_id, entity_type, severity (CRITICAL/HIGH/MEDIUM/LOW), "
                    "mitre_tactic (e.g. TA0008), mitre_technique (e.g. T1021), "
                    "description, confidence (0-1), deviation_score."
                ),
            },
            "source_type": {
                "type": "string",
                "enum": ["anomaly", "soar", "manual", "threat_intel", "edr"],
                "description": "Source of the alert. Default: anomaly.",
            },
        },
        "required": ["alert_data"],
    },
}

IR_CONTAIN_SCHEMA = {
    "name": "ir_execute_containment",
    "description": (
        "Execute containment actions on an active incident. Actions include: "
        "isolate endpoint, revoke credentials, block IP, kill process, disable service, "
        "quarantine file. Supports simulate, execute, and approve modes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The IR incident ID (e.g. IR-A1B2C3D4)."},
            "mode": {
                "type": "string",
                "enum": ["simulate", "execute", "approve"],
                "description": "Execution mode. simulate=dry-run, execute=real action, approve=queue for human approval.",
            },
            "action_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific containment action IDs to execute. Omit to use all recommended.",
            },
            "target": {"type": "string", "description": "Override target (IP, hostname, username, process name)."},
        },
        "required": ["incident_id"],
    },
}

IR_ESCALATE_SCHEMA = {
    "name": "ir_escalate_incident",
    "description": (
        "Escalate an incident to the SOC team via the messaging gateway (Telegram, "
        "Discord, Slack, etc.). Sends a formatted alert with incident details, "
        "containment status, and SLA timers. CRITICAL incidents go to the war room."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The IR incident ID to escalate."},
        },
        "required": ["incident_id"],
    },
}

IR_INVESTIGATE_SCHEMA = {
    "name": "ir_investigate",
    "description": (
        "Compile an investigation report for an incident — correlates containment "
        "results, escalation responses, alert data, and generates remediation "
        "recommendations including CERT-In reporting requirements."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The IR incident ID to investigate."},
            "notes": {"type": "string", "description": "Analyst notes to attach to the investigation."},
        },
        "required": ["incident_id"],
    },
}

IR_AUTO_RESPOND_SCHEMA = {
    "name": "ir_auto_respond",
    "description": (
        "Run the FULL autonomous incident response pipeline in one call: "
        "triage the alert → execute containment actions → escalate to SOC. "
        "Use this for hands-free response to behavioral anomalies and security alerts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "alert_data": {
                "type": "object",
                "description": (
                    "Alert details: entity_id, entity_type, severity, mitre_tactic, "
                    "mitre_technique, description, confidence."
                ),
            },
            "mode": {
                "type": "string",
                "enum": ["simulate", "execute"],
                "description": "simulate=dry-run all actions, execute=real containment. Default: simulate.",
            },
        },
        "required": ["alert_data"],
    },
}

IR_CLOSE_SCHEMA = {
    "name": "ir_close_incident",
    "description": (
        "Close an incident with a resolution summary. Generates the final "
        "incident timeline and marks the case as resolved."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The IR incident ID to close."},
            "resolution": {"type": "string", "description": "Resolution summary (e.g. 'Contained and remediated')."},
        },
        "required": ["incident_id"],
    },
}

IR_SUMMARY_SCHEMA = {
    "name": "ir_dashboard_summary",
    "description": (
        "Get an aggregate dashboard summary of all incident response cases — "
        "counts by phase (TRIAGE/CONTAINMENT/ESCALATION/INVESTIGATION/RECOVERY/CLOSED), "
        "severity distribution, and available containment actions."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# =============================================================================
# Register Tools
# =============================================================================

registry.register(
    name="ir_triage_alert",
    toolset="incident_response",
    schema=IR_TRIAGE_SCHEMA,
    handler=ir_triage_handler,
    check_fn=check_incident_response_requirements,
    emoji="🚨",
)

registry.register(
    name="ir_execute_containment",
    toolset="incident_response",
    schema=IR_CONTAIN_SCHEMA,
    handler=ir_contain_handler,
    check_fn=check_incident_response_requirements,
    emoji="🛡️",
)

registry.register(
    name="ir_escalate_incident",
    toolset="incident_response",
    schema=IR_ESCALATE_SCHEMA,
    handler=ir_escalate_handler,
    check_fn=check_incident_response_requirements,
    emoji="📢",
)

registry.register(
    name="ir_investigate",
    toolset="incident_response",
    schema=IR_INVESTIGATE_SCHEMA,
    handler=ir_investigate_handler,
    check_fn=check_incident_response_requirements,
    emoji="🔍",
)

registry.register(
    name="ir_auto_respond",
    toolset="incident_response",
    schema=IR_AUTO_RESPOND_SCHEMA,
    handler=ir_auto_respond_handler,
    check_fn=check_incident_response_requirements,
    emoji="⚡",
)

registry.register(
    name="ir_close_incident",
    toolset="incident_response",
    schema=IR_CLOSE_SCHEMA,
    handler=ir_close_handler,
    check_fn=check_incident_response_requirements,
    emoji="✅",
)

registry.register(
    name="ir_dashboard_summary",
    toolset="incident_response",
    schema=IR_SUMMARY_SCHEMA,
    handler=ir_summary_handler,
    check_fn=check_incident_response_requirements,
    emoji="📊",
)
