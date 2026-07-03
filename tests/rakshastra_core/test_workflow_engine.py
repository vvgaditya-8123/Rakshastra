import pytest
import tempfile
import uuid
import json
from pathlib import Path
from datetime import datetime

from rakshastra_core.models.workflow import WorkflowState, WorkflowStep
from rakshastra_core.models import Asset, AssetType, AssetRelation, Severity, Evidence
from rakshastra_core.engines import SecurityWorkflowEngine, SecurityReasoningEngine, InfrastructureGraph, ThreatEngine, EvidenceStore
from tools.security_workflow_tool import _handle_security_workflow

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "security.db"

def test_workflow_transitions(temp_db):
    engine = SecurityWorkflowEngine(temp_db)
    session_id = "test_session_1"

    # Default phase is Recon
    assert engine.get_active_phase(session_id) == WorkflowState.RECON
    assert engine.get_max_phase_index(session_id) == 0

    # Transition to next phase (Enumeration) should succeed
    assert engine.transition_to(session_id, WorkflowState.ENUMERATION) is True
    assert engine.get_active_phase(session_id) == WorkflowState.ENUMERATION
    assert engine.get_max_phase_index(session_id) == 1

    # Transitioning to a skipped phase (e.g. Analysis) should fail
    assert engine.transition_to(session_id, WorkflowState.ANALYSIS) is False
    assert engine.get_active_phase(session_id) == WorkflowState.ENUMERATION

    # Transitioning backward to Recon should always succeed
    assert engine.transition_to(session_id, WorkflowState.RECON) is True
    assert engine.get_active_phase(session_id) == WorkflowState.RECON
    # Max phase reached should remain 1 (Enumeration)
    assert engine.get_max_phase_index(session_id) == 1

    # Transitioning forward to Enumeration again should succeed
    assert engine.transition_to(session_id, WorkflowState.ENUMERATION) is True
    # Transitioning forward to Collection should succeed
    assert engine.transition_to(session_id, WorkflowState.COLLECTION) is True
    assert engine.get_active_phase(session_id) == WorkflowState.COLLECTION
    assert engine.get_max_phase_index(session_id) == 2

def test_workflow_step_logging(temp_db):
    engine = SecurityWorkflowEngine(temp_db)
    session_id = "test_session_2"

    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=WorkflowState.RECON,
        command="nmap -sn 10.0.0.0/24",
        status="completed",
        duration=1.5,
        output_summary="Found 3 hosts"
    )

    step_id = engine.log_step(step)
    assert step_id == step.id

    history = engine.get_history(session_id)
    assert len(history) == 1
    assert history[0].command == "nmap -sn 10.0.0.0/24"
    assert history[0].phase == WorkflowState.RECON
    assert history[0].status == "completed"

def test_reasoning_engine(temp_db):
    wf_engine = SecurityWorkflowEngine(temp_db)
    reasoning = SecurityReasoningEngine()
    session_id = "test_session_3"

    # Recon guidelines
    guidance = reasoning.get_guidance(session_id, wf_engine)
    assert guidance["current_phase"] == "Recon"
    assert "network-scan" in guidance["recommended_skills"]
    assert guidance["next_logical_phase"] == "Enumeration"

    # Go to Enumeration
    wf_engine.transition_to(session_id, WorkflowState.ENUMERATION)
    guidance = reasoning.get_guidance(session_id, wf_engine)
    assert guidance["current_phase"] == "Enumeration"
    assert guidance["next_logical_phase"] == "Collection"

def test_connected_memory_graph(temp_db):
    graph = InfrastructureGraph(temp_db)
    
    host = Asset(id="h1", name="prod-web-01", asset_type=AssetType.HOST, ip_address="192.168.1.100")
    container = Asset(id="c1", name="apache-docker", asset_type=AssetType.CONTAINER)
    service = Asset(id="s1", name="apache-httpd", asset_type=AssetType.SERVICE)
    vuln = Asset(id="v1", name="CVE-2021-41773", asset_type=AssetType.VULNERABILITY)
    incident = Asset(id="i1", name="Web Shell Upload", asset_type=AssetType.INCIDENT)
    evidence = Asset(id="e1", name="access_log_alert", asset_type=AssetType.EVIDENCE)
    report = Asset(id="r1", name="Assessment Report", asset_type=AssetType.REPORT)

    graph.link_investigation_chain(
        host=host,
        container=container,
        service=service,
        vulnerability=vuln,
        incident=incident,
        evidence=evidence,
        report=report
    )

    # Validate neighbors traversal
    n_info = graph.neighbors("h1", depth=6)
    assets = n_info["assets"]
    relations = n_info["relations"]

    # All nodes should be present and linked
    assert "h1" in assets
    assert "c1" in assets
    assert "s1" in assets
    assert "v1" in assets
    assert "i1" in assets
    assert "e1" in assets
    assert "r1" in assets

    # Check relation connection types
    rel_types = [r["relation_type"] for r in relations]
    assert "runs_container" in rel_types
    assert "runs_service" in rel_types
    assert "has_vulnerability" in rel_types
    assert "triggers_incident" in rel_types
    assert "proves_incident" in rel_types
    assert "documented_in" in rel_types

def test_threat_engine_connected_memory(temp_db):
    store = EvidenceStore(temp_db)
    graph = InfrastructureGraph(temp_db)
    threat_engine = ThreatEngine(store, graph)

    ev = Evidence(
        tool="nmap",
        host="192.168.1.200",
        timestamp=datetime.utcnow().isoformat() + "Z",
        finding="Exposed Apache HTTP Server containing CVE-2021-41773.",
        raw_output="nmap report details",
        severity=Severity.CRITICAL,
        tags=["cve-2021-41773", "apache", "web"]
    )
    eid = store.record(ev)

    risks = threat_engine.assess(evidence_ids=[eid])
    assert len(risks) == 1

    # Verify that the threat engine automatically created and linked nodes in the InfrastructureGraph
    # 1. Host asset
    host_assets = graph.find_assets(asset_type=AssetType.HOST)
    assert len(host_assets) == 1
    assert host_assets[0].ip_address == "192.168.1.200"

    # 2. Evidence asset
    ev_assets = graph.find_assets(asset_type=AssetType.EVIDENCE)
    assert len(ev_assets) == 1
    assert ev_assets[0].id == eid

    # 3. Vulnerability asset
    vuln_assets = graph.find_assets(asset_type=AssetType.VULNERABILITY)
    assert len(vuln_assets) == 1
    assert vuln_assets[0].name == "CVE-2021-41773"

    # 4. Incident asset (because severity is CRITICAL)
    inc_assets = graph.find_assets(asset_type=AssetType.INCIDENT)
    assert len(inc_assets) == 1
    assert "Incident:" in inc_assets[0].name

    # Validate connections in neighbors
    n_info = graph.neighbors(host_assets[0].id, depth=2)
    rel_types = [r["relation_type"] for r in n_info["relations"]]
    assert "proves_vulnerability" in rel_types
    assert "has_vulnerability" in rel_types
    assert "triggers_incident" in rel_types

def test_workflow_tool_handler(temp_db, monkeypatch):
    monkeypatch.setenv("RAKSHASTRA_SESSION_ID", "tool_test_session")
    
    # Mock home path so the tool uses our temp DB
    from rakshastra_constants import get_rakshastra_home
    monkeypatch.setattr("tools.security_workflow_tool.get_rakshastra_home", lambda: temp_db.parent)

    # 1. Get initial state
    res_str = _handle_security_workflow({"action": "get_state"}, session_id="tool_test_session")
    res = json.loads(res_str)
    assert res["success"] is True
    assert res["current_phase"] == "Recon"

    # 2. Log step
    res_str = _handle_security_workflow({
        "action": "log_step",
        "phase": "Recon",
        "command": "whoami",
        "status": "completed",
        "duration": 0.1,
        "output_summary": "root"
    }, session_id="tool_test_session")
    res = json.loads(res_str)
    assert res["success"] is True
    assert "logged_step_id" in res

    # 3. Transition state
    res_str = _handle_security_workflow({
        "action": "transition_state",
        "phase": "Enumeration"
    }, session_id="tool_test_session")
    res = json.loads(res_str)
    assert res["success"] is True
    assert res["transitioned_to"] == "Enumeration"

    # 4. Get history
    res_str = _handle_security_workflow({"action": "get_history"}, session_id="tool_test_session")
    res = json.loads(res_str)
    assert res["success"] is True
    assert len(res["history"]) == 1
    assert res["history"][0]["command"] == "whoami"
