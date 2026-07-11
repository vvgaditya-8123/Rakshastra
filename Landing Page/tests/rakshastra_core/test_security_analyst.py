import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from rakshastra_core.models import (
    Evidence, Severity, Confidence, Asset, AssetType, AssetRelation, Scan, Incident, Report
)
from rakshastra_core.engines import EvidenceStore, InfrastructureGraph, ThreatEngine

def test_models_to_from_dict():
    # Test Evidence with reproducibility fields
    ev = Evidence(
        tool="nmap",
        host="192.168.1.10",
        timestamp=datetime.utcnow().isoformat() + "Z",
        finding="Port 22/SSH is open",
        raw_output="22/tcp open  ssh",
        severity=Severity.HIGH,
        confidence=Confidence.CONFIRMED,
        tags=["network", "ssh"],
        context={"port": 22},
        collector_version="7.94",
        command="nmap -sV 192.168.1.10",
        duration=12.5,
        exit_code=0,
        checksum="abc123def456",
        platform="linux"
    )
    d = ev.to_dict()
    assert d["tool"] == "nmap"
    assert d["severity"] == "HIGH"
    assert d["tags"] == ["network", "ssh"]
    assert d["collector_version"] == "7.94"
    assert d["command"] == "nmap -sV 192.168.1.10"
    assert d["duration"] == 12.5
    assert d["exit_code"] == 0
    assert d["checksum"] == "abc123def456"
    assert d["platform"] == "linux"
    
    ev2 = Evidence.from_dict(d)
    assert ev2.tool == "nmap"
    assert ev2.severity == Severity.HIGH
    assert ev2.confidence == Confidence.CONFIRMED
    assert ev2.context == {"port": 22}
    assert ev2.collector_version == "7.94"
    assert ev2.platform == "linux"

def test_evidence_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = EvidenceStore(db_path)
        
        # Test record & get with reproducibility fields
        ev = Evidence(
            tool="scanner",
            host="10.0.0.1",
            timestamp="2026-07-02T12:00:00Z",
            finding="Missing security patch",
            severity=Severity.HIGH,
            tags=["patch", "cve"],
            collector_version="1.0.0",
            command="scanner --full 10.0.0.1",
            duration=45.2,
            exit_code=0,
            checksum="sha256:deadbeef",
            platform="linux"
        )
        store.record(ev)
        
        ev_fetched = store.get(ev.id)
        assert ev_fetched is not None
        assert ev_fetched.finding == "Missing security patch"
        assert ev_fetched.severity == Severity.HIGH
        assert ev_fetched.collector_version == "1.0.0"
        assert ev_fetched.command == "scanner --full 10.0.0.1"
        assert ev_fetched.duration == 45.2
        assert ev_fetched.exit_code == 0
        assert ev_fetched.checksum == "sha256:deadbeef"
        assert ev_fetched.platform == "linux"
        
        # Test query
        results = store.query(host="10.0.0.1")
        assert len(results) == 1
        assert results[0].host == "10.0.0.1"
        
        # Test summary
        summary = store.summary()
        assert summary["total"] == 1
        assert summary["by_severity"]["HIGH"] == 1

def test_infrastructure_graph():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        graph = InfrastructureGraph(db_path)
        
        # Add assets
        a1 = Asset(name="DB Server", asset_type=AssetType.DATABASE, hostname="db-1", ip_address="10.0.0.5", properties={"criticality": "high"}, tags=["prod"])
        a2 = Asset(name="Web Server", asset_type=AssetType.HOST, hostname="web-1", ip_address="10.0.0.6", tags=["prod"])
        graph.add_asset(a1)
        graph.add_asset(a2)
        
        # Add relation
        rel = AssetRelation(source_id=a2.id, target_id=a1.id, relation_type="connects_to")
        graph.add_relation(rel)
        
        # Find
        found = graph.find_assets(query="DB")
        assert len(found) == 1
        assert found[0].name == "DB Server"
        
        # Neighbors
        nb = graph.neighbors(a2.id, depth=1)
        assert a1.id in nb["assets"]
        
        # Attack surface
        surface = graph.attack_surface(a2.id)
        assert len(surface) == 1
        assert surface[0].id == a1.id
        
        # Mermaid
        mermaid = graph.to_mermaid()
        assert "DB Server" in mermaid
        assert "Web Server" in mermaid

def test_threat_engine_six_factor_scoring():
    """Validate the six-factor risk formula:
    Risk = Likelihood × Impact × Exploitability × Exposure
           × Business Criticality × Internet Exposure
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = EvidenceStore(db_path)
        graph = InfrastructureGraph(db_path)
        
        # Add an asset with high criticality so the engine can derive business_criticality
        server = Asset(
            name="Prod Web Server",
            asset_type=AssetType.HOST,
            hostname="web-prod",
            ip_address="10.0.0.6",
            properties={"criticality": "critical"},
            tags=["production"]
        )
        graph.add_asset(server)
        
        engine = ThreatEngine(store, graph)
        
        # Add exposed credential on a known host
        ev = Evidence(
            tool="cred_scan",
            host="10.0.0.6",
            timestamp="2026-07-02T12:00:00Z",
            finding="Found secret key exposed in .env",
            severity=Severity.HIGH,
            tags=["credential", "secret", "exposed"],
            collector_version="2.0.0",
            command="cred_scan --deep /srv/app",
            duration=8.3,
            exit_code=0,
            checksum="sha256:abc123",
            platform="linux"
        )
        store.record(ev)
        
        risks = engine.assess()
        assert len(risks) == 1
        risk = risks[0]
        
        # Verify new factors exist
        assert risk.exploitability > 0.0
        assert risk.exposure > 0.0
        assert risk.business_criticality > 0.0
        assert risk.internet_exposure >= 0.0
        
        # Credential + exposed tags should boost exploitability and internet_exposure
        assert risk.exploitability >= 0.7
        assert risk.internet_exposure > 0.0  # "exposed" tag triggers this
        
        # Business criticality should be derived from the asset's "critical" property
        assert risk.business_criticality == 1.0
        
        # Title should reflect exposed credential
        assert "Exposed Credential" in risk.title
        assert "TA0006" in risk.mitre_tactics

def test_threat_engine_without_graph():
    """Ensure ThreatEngine works without infrastructure graph (standalone mode)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = EvidenceStore(db_path)
        engine = ThreatEngine(store)  # No graph
        
        ev = Evidence(
            tool="lynis",
            host="server-1",
            timestamp="2026-07-02T12:00:00Z",
            finding="SSH root login enabled",
            severity=Severity.MEDIUM,
            tags=["ssh", "hardening"],
            command="lynis audit system",
            exit_code=0,
            platform="linux"
        )
        store.record(ev)
        
        risks = engine.assess()
        assert len(risks) == 1
        assert risks[0].risk_score > 0.0
        assert risks[0].business_criticality == 0.5  # default when no graph
