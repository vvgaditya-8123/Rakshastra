"""APT Attribution Service — Full Pipeline Orchestrator.

Orchestrates the complete APT attribution and prediction pipeline:
  1. MITRE ATT&CK knowledge graph lookup
  2. APT campaign attribution
  3. Next-stage move prediction
  4. RAG threat intelligence context retrieval
  5. Attack path analysis
  6. SOAR playbook selection and incident creation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from rakshastra_core.engines.mitre_attack_store import MitreAttackStore
from rakshastra_core.engines.apt_attribution import APTAttributionEngine
from rakshastra_core.engines.attack_predictor import AttackPredictorEngine
from rakshastra_core.engines.soar_engine import SOAREngine
from rakshastra_core.intelligence.threat_intel_rag import ThreatIntelRAG


def _default_db_dir() -> Path:
    """Return the default database directory inside user home."""
    p = Path.home() / ".rakshastra" / "data" / "apt"
    p.mkdir(parents=True, exist_ok=True)
    return p


class APTAttributionService:
    """Orchestrates the full APT attribution and prediction pipeline."""

    def __init__(
        self,
        db_dir: Optional[str] = None,
        mitre_store: Optional[MitreAttackStore] = None,
        rag_store: Optional[ThreatIntelRAG] = None,
        soar_engine: Optional[SOAREngine] = None,
    ):
        base = Path(db_dir) if db_dir else _default_db_dir()
        base.mkdir(parents=True, exist_ok=True)

        self.mitre_store = mitre_store or MitreAttackStore(str(base / "mitre_attack.db"))
        self.attribution_engine = APTAttributionEngine(self.mitre_store)
        self.predictor_engine = AttackPredictorEngine(self.mitre_store)
        self.rag_store = rag_store or ThreatIntelRAG(str(base / "threat_intel_rag.db"))
        self.soar_engine = soar_engine or SOAREngine(str(base / "soar.db"))

    # ── Full Pipeline ────────────────────────────────────────────────────

    def full_analysis(
        self,
        observed_ttps: List[str],
        observed_iocs: Optional[List[str]] = None,
        target_sector: Optional[str] = None,
        target_country: Optional[str] = None,
        org_assets: Optional[List[Dict[str, Any]]] = None,
        create_incident: bool = True,
    ) -> Dict[str, Any]:
        """Run the complete APT attribution and prediction pipeline.

        Returns a comprehensive result with attribution, predictions,
        threat intel context, defensive actions, and SOAR incident.
        """
        observed_iocs = observed_iocs or []

        # Step 1: APT Attribution
        attribution = self.attribution_engine.attribute_campaign(
            observed_ttps=observed_ttps,
            observed_iocs=observed_iocs,
            target_sector=target_sector,
            target_country=target_country,
        )

        # Step 2: Get top attributed group for prediction
        top_group_id = None
        top_group_name = None
        if attribution.get("candidate_groups"):
            top = attribution["candidate_groups"][0]
            top_group_id = top["group_id"]
            top_group_name = top["group_name"]

        # Step 3: Predict next moves
        predictions = self.predictor_engine.predict_next_moves(
            observed_ttps=observed_ttps,
            attributed_group_id=top_group_id,
        )

        # Step 4: Generate defensive actions
        defensive_actions = self.predictor_engine.generate_defensive_actions(
            predictions=predictions,
            org_assets=org_assets,
        )

        # Step 5: Build attack timeline
        timeline = self.predictor_engine.build_attack_timeline(observed_ttps)

        # Step 6: RAG context retrieval
        rag_context = self.rag_store.get_context_for_attribution(
            ttps=observed_ttps,
            iocs=observed_iocs,
            group_name=top_group_name,
        )

        # Step 7: Generate containment plan
        containment_plan = self.soar_engine.generate_containment_plan(
            attributed_apt=attribution,
            predictions=predictions,
            org_assets=org_assets,
        )

        # Step 8: Create SOAR incident (optional)
        incident = None
        if create_incident:
            severity = "CRITICAL" if attribution.get("top_confidence", 0) >= 0.5 else "HIGH"
            incident = self.soar_engine.create_incident(
                alert_data={
                    "observed_ttps": observed_ttps,
                    "observed_iocs": observed_iocs,
                    "target_sector": target_sector,
                    "target_country": target_country,
                },
                severity=severity,
                attribution=attribution,
                mode="simulate",
            )

        return {
            "attribution": attribution,
            "predictions": predictions,
            "defensive_actions": defensive_actions,
            "attack_timeline": timeline,
            "threat_intel_context": rag_context,
            "containment_plan": containment_plan,
            "incident": incident,
            "summary": {
                "attributed_group": top_group_name or "Unknown",
                "attribution_confidence": attribution.get("top_confidence", 0),
                "attribution_status": attribution.get("attribution_status", "UNKNOWN"),
                "current_attack_phase": predictions.get("current_phase", {}).get("tactic_name", "Unknown"),
                "attack_stage": predictions.get("kill_chain_progress", {}).get("estimated_attack_stage", "UNKNOWN"),
                "total_predictions": len(predictions.get("top_predictions", [])),
                "total_defensive_actions": defensive_actions.get("total_actions", 0),
                "critical_actions": defensive_actions.get("critical_actions", 0),
                "rag_documents_found": len(rag_context),
                "incident_id": incident["incident_id"] if incident else None,
            },
        }

    # ── Individual Endpoints ─────────────────────────────────────────────

    def attribute(
        self,
        observed_ttps: List[str],
        observed_iocs: Optional[List[str]] = None,
        target_sector: Optional[str] = None,
        target_country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run only the attribution pipeline."""
        return self.attribution_engine.attribute_campaign(
            observed_ttps=observed_ttps,
            observed_iocs=observed_iocs,
            target_sector=target_sector,
            target_country=target_country,
        )

    def predict(
        self,
        observed_ttps: List[str],
        attributed_group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run only the prediction pipeline."""
        return self.predictor_engine.predict_next_moves(
            observed_ttps=observed_ttps,
            attributed_group_id=attributed_group_id,
        )

    def search_threat_intel(self, query: str, search_type: str = "general", top_k: int = 10) -> List[Dict[str, Any]]:
        """Search the threat intelligence RAG store."""
        if search_type == "cve":
            return self.rag_store.search_by_cve(query)
        elif search_type == "apt_group":
            return self.rag_store.search_by_apt_group(query)
        elif search_type == "source_type":
            return self.rag_store.search_by_source_type(query, limit=top_k)
        else:
            return self.rag_store.search(query, top_k=top_k)

    def get_mitre_techniques(self, tactic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.mitre_store.get_all_techniques(tactic_id)

    def get_mitre_groups(self) -> List[Dict[str, Any]]:
        return self.mitre_store.get_all_groups()

    def get_mitre_tactics(self) -> List[Dict[str, Any]]:
        return self.mitre_store.get_all_tactics()

    def get_group_profile(self, group_id: str) -> Optional[Dict[str, Any]]:
        return self.attribution_engine.get_group_profile(group_id)
