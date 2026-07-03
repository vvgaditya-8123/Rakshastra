from datetime import datetime
from pathlib import Path
from rakshastra_constants import get_rakshastra_home
from rakshastra_core.models import Evidence, Severity, Confidence
from rakshastra_core.engines import EvidenceStore
from tools.registry import registry, tool_result, tool_error

import uuid
import os
from rakshastra_core.engines.workflow import SecurityWorkflowEngine
from rakshastra_core.models.workflow import WorkflowStep

def check_security_requirements() -> bool:
    return True

def _get_evidence_store() -> EvidenceStore:
    db_path = get_rakshastra_home() / "security.db"
    return EvidenceStore(db_path)

def _handle_security_evidence(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")
    db_path = get_rakshastra_home() / "security.db"
    wf_engine = SecurityWorkflowEngine(db_path)
    current_wf_phase = wf_engine.get_active_phase(session_id)
    action = args.get("action", "query").lower()

    res = _handle_security_evidence_inner(args, **kwargs)

    status = "completed" if "error" not in str(res) else "failed"
    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=current_wf_phase,
        command=f"security_evidence(action={action})",
        status=status,
        duration=0.0,
        output_summary=f"Executed security evidence action: {action}."
    )
    wf_engine.log_step(step)
    return res

def _handle_security_evidence_inner(args: dict, **kwargs) -> str:
    action = args.get("action", "query").lower()
    store = _get_evidence_store()

    try:
        if action == "query":
            host = args.get("host")
            sev_str = args.get("severity")
            severity = None
            if sev_str:
                try:
                    severity = Severity(sev_str.upper())
                except ValueError:
                    pass
            tags = args.get("tags")
            
            evidences = store.query(host=host, severity=severity, tags=tags)
            return tool_result(success=True, evidence=[e.to_dict() for e in evidences])

        elif action == "record":
            ev_data = args.get("evidence")
            if not ev_data or not isinstance(ev_data, dict):
                return tool_error("Missing or invalid 'evidence' dict for record action.")
            
            sev_str = ev_data.get("severity", "INFO")
            conf_str = ev_data.get("confidence", "TENTATIVE")
            
            try:
                severity = Severity(sev_str.upper())
            except ValueError:
                severity = Severity.INFO
                
            try:
                confidence = Confidence(conf_str.upper())
            except ValueError:
                confidence = Confidence.TENTATIVE
            
            ev = Evidence(
                tool=ev_data.get("tool", "manual"),
                host=ev_data.get("host", "localhost"),
                timestamp=ev_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                finding=ev_data.get("finding", ""),
                raw_output=ev_data.get("raw_output", ""),
                severity=severity,
                confidence=confidence,
                tags=ev_data.get("tags", []),
                context=ev_data.get("context", {})
            )
            eid = store.record(ev)
            return tool_result(success=True, evidence_id=eid, message="Evidence recorded successfully.")

        elif action == "summary":
            summ = store.summary()
            return tool_result(success=True, summary=summ)

        else:
            return tool_error(f"Unknown evidence action: {action}")

    except Exception as e:
        return tool_error(f"Failed to manage security evidence: {str(e)}")

SECURITY_EVIDENCE_SCHEMA = {
    "name": "security_evidence",
    "description": "Queries, filters, and manually records security findings in the Evidence Store.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["query", "record", "summary"],
                "default": "query",
                "description": "The action to perform (query findings, manually record new finding, or retrieve summary)."
            },
            "host": {
                "type": "string",
                "description": "Filter by target host IP or hostname (for query action)."
            },
            "severity": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
                "description": "Filter by severity level (for query action)."
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by specific tags (for query action)."
            },
            "evidence": {
                "type": "object",
                "description": "The evidence details to record. Keys: tool, host, finding, raw_output, severity, confidence, tags, context."
            }
        },
        "required": ["action"]
    }
}

registry.register(
    name="security_evidence",
    toolset="security",
    schema=SECURITY_EVIDENCE_SCHEMA,
    handler=_handle_security_evidence,
    check_fn=check_security_requirements,
    emoji="📊"
)
