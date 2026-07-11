from typing import List, Dict, Any, Optional
from rakshastra_core.models import Evidence, Risk, Severity, Confidence, Asset, AssetType, AssetRelation
from rakshastra_core.engines.evidence import EvidenceStore
from rakshastra_core.engines.infrastructure_graph import InfrastructureGraph

class ThreatEngine:
    """Converts collected evidence into prioritized risks with attack paths.

    Risk scoring uses a six-factor formula:
        Risk = Likelihood × Impact × Exploitability × Exposure
               × Business Criticality × Internet Exposure
    scaled to 0–10.
    """

    def __init__(self, evidence_store: EvidenceStore,
                 infrastructure_graph: Optional[InfrastructureGraph] = None):
        self.evidence_store = evidence_store
        self.infrastructure_graph = infrastructure_graph

    def assess(self, evidence_ids: List[str] = None) -> List[Risk]:
        """Compute risk assessments from evidence."""
        evidences = []
        if evidence_ids:
            for eid in evidence_ids:
                ev = self.evidence_store.get(eid)
                if ev:
                    evidences.append(ev)
        else:
            evidences = self.evidence_store.query()

        risks: List[Risk] = []

        for ev in evidences:
            title = f"Vulnerability detected: {ev.finding[:60]}"
            description = ev.finding
            mitre_tactics = []
            recommended_actions = []

            # ── Base factor seeding from severity ──────────────────────
            likelihood = 0.5
            impact = 0.5
            exploitability = 0.5
            exposure = 0.5
            business_criticality = 0.5
            internet_exposure = 0.0

            if ev.severity == Severity.CRITICAL:
                likelihood, impact, exploitability = 0.9, 0.9, 0.8
            elif ev.severity == Severity.HIGH:
                likelihood, impact, exploitability = 0.8, 0.75, 0.7
            elif ev.severity == Severity.MEDIUM:
                likelihood, impact, exploitability = 0.6, 0.6, 0.5
            elif ev.severity == Severity.LOW:
                likelihood, impact, exploitability = 0.4, 0.4, 0.3
            else:
                likelihood, impact, exploitability = 0.2, 0.2, 0.2

            # ── Confidence adjustment ──────────────────────────────────
            if ev.confidence == Confidence.CONFIRMED:
                likelihood = min(1.0, likelihood + 0.1)
            elif ev.confidence == Confidence.TENTATIVE:
                likelihood = max(0.1, likelihood - 0.1)

            # ── Tag-driven MITRE mapping & factor tuning ───────────────
            tags_lower = [t.lower() for t in ev.tags]
            # Title priority: higher number = higher priority (most specific wins)
            title_priority = 0

            # Initial Access / Recon — indicates internet exposure (lowest title priority)
            if any(x in tags_lower for x in ["nmap", "scan", "port", "exposed"]):
                mitre_tactics.append("TA0001")  # Initial Access
                mitre_tactics.append("TA0043")  # Reconnaissance
                recommended_actions.append("Close unnecessary exposed ports at the firewall layer.")
                recommended_actions.append("Restrict network access to authorized IPs only.")
                exposure = min(1.0, exposure + 0.2)
                internet_exposure = min(1.0, internet_exposure + 0.5)
                if title_priority < 1:
                    title = f"Network Exposure: {ev.finding[:60]}"
                    title_priority = 1

            # Privilege Escalation / Execution
            if any(x in tags_lower for x in ["privileged", "suid", "docker-socket", "escalation"]):
                mitre_tactics.append("TA0004")  # Privilege Escalation
                mitre_tactics.append("TA0002")  # Execution
                recommended_actions.append("Run container without privilege flags.")
                recommended_actions.append("Restrict SUID permissions and monitor process actions.")
                impact = min(1.0, impact + 0.1)
                exploitability = min(1.0, exploitability + 0.15)
                if title_priority < 2:
                    title = f"Privilege Escalation Vector: {ev.finding[:60]}"
                    title_priority = 2

            # Known CVE
            if any(x.startswith("cve-") for x in tags_lower):
                cve_tag = next((x for x in tags_lower if x.startswith("cve-")), "CVE")
                mitre_tactics.append("TA0002")  # Execution
                recommended_actions.append(f"Upgrade package/dependency to remediate {cve_tag.upper()}.")
                exploitability = min(1.0, exploitability + 0.2)
                if title_priority < 3:
                    title = f"Known Vulnerability ({cve_tag.upper()}): {ev.finding[:60]}"
                    title_priority = 3

            # Credential Access (highest title priority)
            if any(x in tags_lower for x in ["credential", "password", "key", "token", "secret"]):
                mitre_tactics.append("TA0006")  # Credential Access
                recommended_actions.append("Revoke the exposed key/token immediately.")
                recommended_actions.append("Rotate and update credentials in all referencing services.")
                likelihood = min(1.0, likelihood + 0.1)
                impact = min(1.0, impact + 0.15)
                exploitability = min(1.0, exploitability + 0.2)  # credentials are trivially exploitable
                if title_priority < 4:
                    title = f"Exposed Credential/Secret: {ev.finding[:60]}"
                    title_priority = 4

            # ── Infrastructure Graph enrichment ────────────────────────
            attack_path = []
            if self.infrastructure_graph and ev.host:
                matched_assets = self.infrastructure_graph.find_assets(query=ev.host)
                if matched_assets:
                    target_asset = matched_assets[0]
                else:
                    # Create the Host asset if it doesn't exist
                    target_asset = Asset(
                        name=f"Host: {ev.host}",
                        asset_type=AssetType.HOST,
                        hostname=ev.host if not ev.host.replace(".", "").isdigit() else None,
                        ip_address=ev.host if ev.host.replace(".", "").isdigit() else None,
                        properties={},
                        tags=[]
                    )
                    self.infrastructure_graph.add_asset(target_asset)

                # 1. Create and link EVIDENCE node
                evidence_asset = Asset(
                    id=ev.id,
                    name=f"Evidence: {ev.tool}",
                    asset_type=AssetType.EVIDENCE,
                    properties={"finding": ev.finding, "tool": ev.tool, "severity": ev.severity.value},
                    tags=ev.tags
                )
                self.infrastructure_graph.add_asset(evidence_asset)
                self.infrastructure_graph.add_relation(AssetRelation(
                    source_id=target_asset.id,
                    target_id=evidence_asset.id,
                    relation_type="proves_vulnerability"
                ))

                # 2. If CVE tag is present, create and link VULNERABILITY node
                cve_tag = next((t for t in tags_lower if t.startswith("cve-")), None)
                if cve_tag:
                    vuln_asset = Asset(
                        name=cve_tag.upper(),
                        asset_type=AssetType.VULNERABILITY,
                        properties={"cve": cve_tag.upper(), "description": ev.finding},
                        tags=[cve_tag]
                    )
                    self.infrastructure_graph.add_asset(vuln_asset)
                    self.infrastructure_graph.add_relation(AssetRelation(
                        source_id=target_asset.id,
                        target_id=vuln_asset.id,
                        relation_type="has_vulnerability"
                    ))
                    self.infrastructure_graph.add_relation(AssetRelation(
                        source_id=vuln_asset.id,
                        target_id=evidence_asset.id,
                        relation_type="evidenced_by"
                    ))

                # 3. If Severity is HIGH or CRITICAL, create and link INCIDENT node
                if ev.severity in [Severity.CRITICAL, Severity.HIGH]:
                    incident_asset = Asset(
                        name=f"Incident: {title}",
                        asset_type=AssetType.INCIDENT,
                        properties={"status": "open", "description": ev.finding, "severity": ev.severity.value},
                        tags=["security-incident"]
                    )
                    self.infrastructure_graph.add_asset(incident_asset)
                    self.infrastructure_graph.add_relation(AssetRelation(
                        source_id=target_asset.id,
                        target_id=incident_asset.id,
                        relation_type="triggers_incident"
                    ))
                    self.infrastructure_graph.add_relation(AssetRelation(
                        source_id=incident_asset.id,
                        target_id=evidence_asset.id,
                        relation_type="documented_by"
                    ))

                # Derive business_criticality from asset properties
                crit = target_asset.properties.get("criticality", "").lower()
                if crit == "critical":
                    business_criticality = 1.0
                elif crit == "high":
                    business_criticality = 0.8
                elif crit == "medium":
                    business_criticality = 0.5
                elif crit == "low":
                    business_criticality = 0.3

                attack_path.append(f"External/Attacker -> {target_asset.name}")
                downstream = self.infrastructure_graph.attack_surface(target_asset.id)
                for ds_asset in downstream[:3]:
                    attack_path.append(f"{target_asset.name} -> {ds_asset.name}")
            else:
                attack_path.append(f"External/Attacker -> Host: {ev.host}")

            # ── Six-factor composite risk score ────────────────────────
            # Base score: Likelihood × Impact (classic risk formula, 0–10 range)
            # Modifier: geometric mean of the remaining four factors
            # This prevents the 6-way product from collapsing to near-zero
            # while still letting all six factors influence the final score.
            ie_factor = max(internet_exposure, 0.1)  # floor to avoid zeroing
            base_score = likelihood * impact * 10
            modifier = (exploitability * exposure * business_criticality * ie_factor) ** 0.25
            risk_score = round(base_score * modifier, 1)

            # Derive severity label from composite score
            derived_severity = Severity.INFO
            if risk_score >= 8.0:
                derived_severity = Severity.CRITICAL
            elif risk_score >= 5.0:
                derived_severity = Severity.HIGH
            elif risk_score >= 2.0:
                derived_severity = Severity.MEDIUM
            elif risk_score >= 0.5:
                derived_severity = Severity.LOW

            risk_obj = Risk(
                title=title,
                description=description,
                evidence_ids=[ev.id],
                likelihood=likelihood,
                impact=impact,
                exploitability=exploitability,
                exposure=exposure,
                business_criticality=business_criticality,
                internet_exposure=internet_exposure,
                risk_score=risk_score,
                severity=derived_severity,
                recommended_actions=recommended_actions,
                attack_path=attack_path,
                mitre_tactics=mitre_tactics
            )
            risk_obj.created_at = ev.created_at
            risks.append(risk_obj)

        return self.prioritize(risks)

    def prioritize(self, risks: List[Risk]) -> List[Risk]:
        """Sort risks by composite score descending."""
        return sorted(risks, key=lambda r: r.risk_score, reverse=True)
