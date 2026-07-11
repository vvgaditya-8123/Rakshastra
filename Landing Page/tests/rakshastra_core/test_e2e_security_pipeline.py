"""End-to-End Integration Test — Full Security Pipeline

Validates the complete chain:
    Trigger security_scan → Record Evidence → Assess with ThreatEngine
    → Enrich via InfrastructureGraph → Generate Report

Every stage is validated for data integrity and flow correctness.
No mocks — real SQLite databases, real engines.
"""

import hashlib
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from rakshastra_core.models import (
    Asset, AssetType, AssetRelation, Evidence, Severity, Confidence, Report
)
from rakshastra_core.engines import EvidenceStore, InfrastructureGraph, ThreatEngine


class TestE2ESecurityPipeline:
    """Complete pipeline: Evidence → ThreatEngine → InfrastructureGraph → Report."""

    @pytest.fixture(autouse=True)
    def setup_pipeline(self, tmp_path):
        """Create a fresh, isolated database and all engines for each test."""
        self.db_path = tmp_path / "e2e_security.db"
        self.store = EvidenceStore(self.db_path)
        self.graph = InfrastructureGraph(self.db_path)
        self.engine = ThreatEngine(self.store, self.graph)

    # ──────────────────────────────────────────────────────────────────────
    # Stage 1: Infrastructure topology
    # ──────────────────────────────────────────────────────────────────────
    def _build_infrastructure(self):
        """Build a realistic 4-node infrastructure topology."""
        self.firewall = Asset(
            name="Edge Firewall", asset_type=AssetType.HOST,
            hostname="fw-edge-01", ip_address="203.0.113.1",
            properties={"criticality": "critical", "vendor": "pfsense"},
            tags=["perimeter", "production"]
        )
        self.web = Asset(
            name="Production Web Server", asset_type=AssetType.HOST,
            hostname="web-prod-01", ip_address="10.0.1.10",
            properties={"criticality": "high", "os": "ubuntu-22.04"},
            tags=["production", "web"]
        )
        self.app = Asset(
            name="Application Server", asset_type=AssetType.HOST,
            hostname="app-prod-01", ip_address="10.0.2.20",
            properties={"criticality": "high", "runtime": "python-3.11"},
            tags=["production", "app"]
        )
        self.db = Asset(
            name="Primary Database", asset_type=AssetType.DATABASE,
            hostname="db-prod-01", ip_address="10.0.3.30",
            properties={"criticality": "critical", "engine": "postgresql"},
            tags=["production", "database", "pii"]
        )

        for asset in [self.firewall, self.web, self.app, self.db]:
            self.graph.add_asset(asset)

        # Firewall → Web → App → DB (attack path topology)
        self.graph.add_relation(AssetRelation(
            source_id=self.firewall.id, target_id=self.web.id,
            relation_type="routes_to"
        ))
        self.graph.add_relation(AssetRelation(
            source_id=self.web.id, target_id=self.app.id,
            relation_type="connects_to"
        ))
        self.graph.add_relation(AssetRelation(
            source_id=self.app.id, target_id=self.db.id,
            relation_type="connects_to"
        ))

    # ──────────────────────────────────────────────────────────────────────
    # Stage 2: Evidence collection (simulating scan results)
    # ──────────────────────────────────────────────────────────────────────
    def _collect_evidence(self):
        """Simulate three scanners producing evidence with reproducibility fields."""
        raw_nmap = "22/tcp open  ssh  OpenSSH 8.9\n80/tcp open  http Apache 2.4.52\n443/tcp open ssl/http Apache 2.4.52"
        self.ev_nmap = Evidence(
            tool="nmap",
            host="10.0.1.10",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="Web server has 3 open ports (22, 80, 443)",
            raw_output=raw_nmap,
            severity=Severity.MEDIUM,
            confidence=Confidence.CONFIRMED,
            tags=["nmap", "port", "exposed", "scan"],
            context={"ports": [22, 80, 443]},
            collector_version="7.94",
            command="nmap -sV -p- 10.0.1.10",
            duration=84.3,
            exit_code=0,
            checksum=hashlib.sha256(raw_nmap.encode()).hexdigest(),
            platform="linux"
        )

        raw_cred = "MATCH: /srv/app/.env contains AWS_SECRET_ACCESS_KEY=AKIA..."
        self.ev_cred = Evidence(
            tool="trufflehog",
            host="10.0.2.20",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="AWS secret key exposed in application .env file",
            raw_output=raw_cred,
            severity=Severity.CRITICAL,
            confidence=Confidence.CONFIRMED,
            tags=["credential", "secret", "aws", "exposed"],
            context={"file": "/srv/app/.env", "key_type": "aws_secret"},
            collector_version="3.63.0",
            command="trufflehog filesystem /srv/app",
            duration=12.1,
            exit_code=1,
            checksum=hashlib.sha256(raw_cred.encode()).hexdigest(),
            platform="linux"
        )

        raw_docker = "Container 'api' running with --privileged flag\nDocker socket mounted at /var/run/docker.sock"
        self.ev_docker = Evidence(
            tool="docker_audit",
            host="10.0.2.20",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="Container running with --privileged and docker socket mount",
            raw_output=raw_docker,
            severity=Severity.HIGH,
            confidence=Confidence.CONFIRMED,
            tags=["docker-socket", "privileged", "escalation", "container"],
            context={"container": "api", "privileged": True},
            collector_version="1.2.0",
            command="docker inspect api",
            duration=2.5,
            exit_code=0,
            checksum=hashlib.sha256(raw_docker.encode()).hexdigest(),
            platform="linux"
        )

        for ev in [self.ev_nmap, self.ev_cred, self.ev_docker]:
            self.store.record(ev)

    # ──────────────────────────────────────────────────────────────────────
    # Tests
    # ──────────────────────────────────────────────────────────────────────

    def test_full_pipeline_evidence_through_report(self):
        """End-to-end: build infra → collect evidence → assess risk → generate report."""
        self._build_infrastructure()
        self._collect_evidence()

        # ── Verify evidence persistence ────────────────────────────────
        all_evidence = self.store.query()
        assert len(all_evidence) == 3, f"Expected 3 evidence items, got {len(all_evidence)}"

        # Verify reproducibility fields survived the round-trip
        fetched_nmap = self.store.get(self.ev_nmap.id)
        assert fetched_nmap.collector_version == "7.94"
        assert fetched_nmap.command == "nmap -sV -p- 10.0.1.10"
        assert fetched_nmap.duration == 84.3
        assert fetched_nmap.exit_code == 0
        assert len(fetched_nmap.checksum) == 64  # SHA-256 hex
        assert fetched_nmap.platform == "linux"

        # ── Verify InfrastructureGraph topology ────────────────────────
        all_assets = self.graph.find_assets()
        assert len(all_assets) == 4, f"Expected 4 assets, got {len(all_assets)}"

        # Attack surface from firewall should reach all downstream nodes
        downstream = self.graph.attack_surface(self.firewall.id)
        downstream_ids = {a.id for a in downstream}
        assert self.web.id in downstream_ids
        assert self.app.id in downstream_ids
        assert self.db.id in downstream_ids

        # ── Assess risks with ThreatEngine ─────────────────────────────
        risks = self.engine.assess()
        assert len(risks) == 3, f"Expected 3 risks, got {len(risks)}"

        # Risks should be sorted by score (descending)
        for i in range(len(risks) - 1):
            assert risks[i].risk_score >= risks[i + 1].risk_score, \
                f"Risk {i} score {risks[i].risk_score} < risk {i+1} score {risks[i+1].risk_score}"

        # ── Verify six-factor scoring on the credential risk ───────────
        cred_risk = next(r for r in risks if "Credential" in r.title)
        assert cred_risk.exploitability > 0.5, "Credential exploitability should be elevated"
        assert cred_risk.internet_exposure > 0.0, "Exposed tag should set internet_exposure"
        # Host 10.0.2.20 matches app-prod-01 with criticality=high → business_criticality=0.8
        assert cred_risk.business_criticality == 0.8, \
            f"Expected business_criticality 0.8, got {cred_risk.business_criticality}"
        assert "TA0006" in cred_risk.mitre_tactics

        # ── Verify attack path enrichment ──────────────────────────────
        # The docker risk is on host 10.0.2.20 → matches "Application Server"
        docker_risk = next(r for r in risks if "Privilege Escalation" in r.title)
        assert any("Application Server" in step for step in docker_risk.attack_path), \
            f"Attack path should reference Application Server, got: {docker_risk.attack_path}"

        # ── Generate Report ────────────────────────────────────────
        summary = self.store.summary()
        report = Report(
            title="E2E Security Assessment",
            report_type="full_assessment",
            executive_summary=(
                f"Assessed {summary['total']} evidence items across "
                f"{len(summary['by_host'])} hosts. "
                f"Identified {len(risks)} risks."
            ),
            findings=[
                {
                    "risk_id": r.id,
                    "title": r.title,
                    "severity": r.severity.value,
                    "score": r.risk_score,
                    "evidence_ids": r.evidence_ids
                }
                for r in risks
            ],
            risk_summary={
                "total": len(risks),
                "critical": sum(1 for r in risks if r.severity == Severity.CRITICAL),
                "high": sum(1 for r in risks if r.severity == Severity.HIGH),
                "medium": sum(1 for r in risks if r.severity == Severity.MEDIUM),
                "low": sum(1 for r in risks if r.severity == Severity.LOW),
            },
            recommendations=[a for r in risks for a in r.recommended_actions]
        )

        assert report.title == "E2E Security Assessment"
        assert report.report_type == "full_assessment"
        assert len(report.findings) == 3
        assert report.risk_summary["total"] == 3
        assert len(report.executive_summary) > 0

    def test_infrastructure_graph_enriches_business_criticality(self):
        """Verify that InfrastructureGraph's asset criticality flows into risk scoring."""
        self._build_infrastructure()

        # Evidence targeting the critical database
        ev = Evidence(
            tool="sqlmap",
            host="10.0.3.30",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="SQL injection on /api/users endpoint",
            severity=Severity.CRITICAL,
            confidence=Confidence.CONFIRMED,
            tags=["sqli", "cve-2024-1234"],
            command="sqlmap -u http://10.0.3.30/api/users --batch",
            exit_code=0,
            platform="linux"
        )
        self.store.record(ev)

        risks = self.engine.assess()
        assert len(risks) == 1
        risk = risks[0]

        # DB has criticality=critical → business_criticality should be 1.0
        assert risk.business_criticality == 1.0
        # CVE tag should boost exploitability
        assert risk.exploitability >= 0.8
        # Attack path should name the database
        assert any("Primary Database" in step for step in risk.attack_path)

    def test_evidence_checksum_integrity(self):
        """Verify that checksums survive storage round-trip for reproducibility."""
        raw = "test output for checksum verification"
        expected_checksum = hashlib.sha256(raw.encode()).hexdigest()

        ev = Evidence(
            tool="integrity_test",
            host="localhost",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="Test finding",
            raw_output=raw,
            severity=Severity.LOW,
            checksum=expected_checksum,
            collector_version="0.0.1",
            platform="windows"
        )
        self.store.record(ev)

        fetched = self.store.get(ev.id)
        assert fetched.checksum == expected_checksum
        # Verify the checksum actually matches the raw output
        assert hashlib.sha256(fetched.raw_output.encode()).hexdigest() == fetched.checksum

    def test_risk_prioritization_order(self):
        """Verify that risks are returned in descending score order."""
        self._build_infrastructure()

        # Low severity finding
        self.store.record(Evidence(
            tool="info_check", host="10.0.1.10",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="Server version disclosed",
            severity=Severity.LOW,
            tags=["info_disclosure"]
        ))

        # Critical severity finding
        self.store.record(Evidence(
            tool="vuln_scan", host="10.0.3.30",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="Remote code execution via deserialization",
            severity=Severity.CRITICAL,
            tags=["rce", "cve-2024-9999", "exposed"],
            confidence=Confidence.CONFIRMED
        ))

        # Medium severity finding
        self.store.record(Evidence(
            tool="ssl_scan", host="10.0.1.10",
            timestamp=datetime.utcnow().isoformat() + "Z",
            finding="TLS 1.0 still accepted",
            severity=Severity.MEDIUM,
            tags=["ssl", "deprecated"]
        ))

        risks = self.engine.assess()
        assert len(risks) == 3

        # Verify descending order
        scores = [r.risk_score for r in risks]
        assert scores == sorted(scores, reverse=True), \
            f"Risks not in descending order: {scores}"

        # The critical RCE with CVE and exposed tags should be first
        assert "cve-2024-9999" in risks[0].title.lower() or risks[0].severity == Severity.CRITICAL
