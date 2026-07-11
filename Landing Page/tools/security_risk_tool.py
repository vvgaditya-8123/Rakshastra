from pathlib import Path
from rakshastra_constants import get_rakshastra_home
from rakshastra_core.engines import EvidenceStore, ThreatEngine, InfrastructureGraph
from tools.registry import registry, tool_result, tool_error

import uuid
import os
from datetime import datetime
from rakshastra_core.engines.workflow import SecurityWorkflowEngine
from rakshastra_core.models.workflow import WorkflowStep

def check_security_requirements() -> bool:
    return True

def _handle_security_risk(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")
    db_path = get_rakshastra_home() / "security.db"
    wf_engine = SecurityWorkflowEngine(db_path)
    current_wf_phase = wf_engine.get_active_phase(session_id)

    res = _handle_security_risk_inner(args, **kwargs)

    status = "completed" if "error" not in str(res) else "failed"
    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=current_wf_phase,
        command="security_risk()",
        status=status,
        duration=0.0,
        output_summary="Executed security risk assessment."
    )
    wf_engine.log_step(step)
    return res

def _handle_security_risk_inner(args: dict, **kwargs) -> str:
    evidence_ids = args.get("evidence_ids")
    
    db_path = get_rakshastra_home() / "security.db"
    store = EvidenceStore(db_path)
    graph = InfrastructureGraph(db_path)
    engine = ThreatEngine(store, graph)

    try:
        risks = engine.assess(evidence_ids=evidence_ids)
        return tool_result(success=True, risks=[r.to_dict() for r in risks])
    except Exception as e:
        return tool_error(f"Failed to assess security risks: {str(e)}")

SECURITY_RISK_SCHEMA = {
    "name": "security_risk",
    "description": "Calculates risk assessments and prioritizes findings based on severity, likelihood, and impact.",
    "parameters": {
        "type": "object",
        "properties": {
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of evidence IDs to restrict threat assessment to."
            }
        }
    }
}

registry.register(
    name="security_risk",
    toolset="security",
    schema=SECURITY_RISK_SCHEMA,
    handler=_handle_security_risk,
    check_fn=check_security_requirements,
    emoji="⚠️"
)
