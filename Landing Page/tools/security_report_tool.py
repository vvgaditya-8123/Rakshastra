import json
from datetime import datetime
from pathlib import Path
from rakshastra_constants import get_rakshastra_home
from rakshastra_core.models import Report, Severity
from rakshastra_core.engines import EvidenceStore, ThreatEngine, InfrastructureGraph
from tools.registry import registry, tool_result, tool_error

import uuid
import os
from rakshastra_core.engines.workflow import SecurityWorkflowEngine
from rakshastra_core.models.workflow import WorkflowState, WorkflowStep

def check_security_requirements() -> bool:
    return True

def _handle_security_report(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")
    db_path = get_rakshastra_home() / "security.db"
    wf_engine = SecurityWorkflowEngine(db_path)
    report_type = args.get("report_type", "vulnerability").lower()
    title = args.get("title", f"Security Audit Report - {datetime.now().strftime('%Y-%m-%d')}")
    exec_summary = args.get("executive_summary", "")
    
    # Gate final report generation until at least Prioritization (index 5) has been reached
    max_phase_idx = wf_engine.get_max_phase_index(session_id)
    if max_phase_idx < 5:
        return tool_error(
            "Report generation blocked. You must progress through preceding investigation phases "
            "up to at least Prioritization before generating a Report."
        )

    # Automatically transition to Report phase
    wf_engine.transition_to(session_id, WorkflowState.REPORT)
    current_wf_phase = wf_engine.get_active_phase(session_id)

    res = _handle_security_report_inner(args, **kwargs)

    status = "completed" if "error" not in str(res) else "failed"
    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=current_wf_phase,
        command="security_report()",
        status=status,
        duration=0.0,
        output_summary="Generated final security report."
    )
    wf_engine.log_step(step)
    
    # Register the generated report asset to the connected memory graph if graph is available
    if "error" not in str(res):
        try:
            report_data = json.loads(res)
            # Find the report ID or file path
            report_id = report_data.get("report_id") or str(uuid.uuid4())
            file_path = report_data.get("file_path", "")
            # Let's add it to the graph
            from rakshastra_core.models import Asset, AssetType, AssetRelation
            graph = InfrastructureGraph(db_path)
            report_node = Asset(
                id=report_id,
                name=f"Report: {title}",
                asset_type=AssetType.REPORT,
                properties={"file_path": file_path, "report_type": report_type},
                tags=["security-report"]
            )
            graph.add_asset(report_node)
            
            # Retrieve risks to link report to evidence nodes
            store = EvidenceStore(db_path)
            engine = ThreatEngine(store, graph)
            risks = engine.assess()
            for r in risks:
                if r.evidence_ids:
                    for ev_id in r.evidence_ids:
                        graph.add_relation(AssetRelation(
                            source_id=ev_id,
                            target_id=report_node.id,
                            relation_type="documented_in"
                        ))
        except Exception:
            pass

    return res

def _handle_security_report_inner(args: dict, **kwargs) -> str:
    report_type = args.get("report_type", "vulnerability").lower()
    title = args.get("title", f"Security Audit Report - {datetime.now().strftime('%Y-%m-%d')}")
    exec_summary = args.get("executive_summary")

    db_path = get_rakshastra_home() / "security.db"
    store = EvidenceStore(db_path)
    graph = InfrastructureGraph(db_path)
    engine = ThreatEngine(store, graph)

    try:
        risks = engine.assess()
        
        total_risks = len(risks)
        critical_count = sum(1 for r in risks if r.severity == Severity.CRITICAL)
        high_count = sum(1 for r in risks if r.severity == Severity.HIGH)
        medium_count = sum(1 for r in risks if r.severity == Severity.MEDIUM)
        low_count = sum(1 for r in risks if r.severity == Severity.LOW)
        
        risk_summary = {
            "total_risks": total_risks,
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count
        }

        if not exec_summary:
            if total_risks > 0:
                exec_summary = (
                    f"A security assessment was performed. A total of {total_risks} risks were identified: "
                    f"{critical_count} Critical, {high_count} High, {medium_count} Medium, and {low_count} Low. "
                    f"Prioritized remediation should address the critical and high findings immediately."
                )
            else:
                exec_summary = "A security assessment was performed. No active risks or open vulnerabilities were identified."

        findings = []
        recommendations = []
        for r in risks:
            findings.append({
                "title": r.title,
                "description": r.description,
                "severity": r.severity.value,
                "risk_score": r.risk_score,
                "attack_path": r.attack_path,
                "mitre_tactics": r.mitre_tactics
            })
            for rec in r.recommended_actions:
                if rec not in recommendations:
                    recommendations.append(rec)

        report = Report(
            title=title,
            report_type=report_type,
            executive_summary=exec_summary,
            findings=findings,
            risk_summary=risk_summary,
            recommendations=recommendations,
            generated_at=datetime.utcnow().isoformat() + "Z"
        )

        reports_dir = get_rakshastra_home() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"report_{report.id}.json"
        report_file.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

        return tool_result(
            success=True,
            report_id=report.id,
            file_path=str(report_file),
            report=report.to_dict()
        )

    except Exception as e:
        return tool_error(f"Failed to generate security report: {str(e)}")

SECURITY_REPORT_SCHEMA = {
    "name": "security_report",
    "description": "Generates structured security assessment reports summarizing findings, executive metrics, and prioritized remediation actions.",
    "parameters": {
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "enum": ["vulnerability", "compliance", "incident"],
                "default": "vulnerability",
                "description": "The type of report to generate."
            },
            "title": {
                "type": "string",
                "description": "The title of the report."
            },
            "executive_summary": {
                "type": "string",
                "description": "Optional custom executive summary text."
            }
        }
    }
}

registry.register(
    name="security_report",
    toolset="security",
    schema=SECURITY_REPORT_SCHEMA,
    handler=_handle_security_report,
    check_fn=check_security_requirements,
    emoji="📄"
)
