from typing import Dict, Any, List

class ThreatPrioritizationEngine:
    """Calculates Intelligence Risk Scores and prioritizes watchlists."""

    def __init__(self):
        pass

    def calculate_risk_score(self, drug_probability: float, automation_confidence: float,
                             platform_count: int, network_size: int, has_financials: bool) -> Dict[str, Any]:
        """Compute threat/risk score based on OSINT parameters.
        
        Formula:
        Risk Score = (Drug Prob * 0.40) + (Automation Conf * 0.15) + (Platform Count * 0.15) + (Network Size * 0.20) + (Financials * 0.10)
        """
        # Normalize inputs
        norm_platform = min(platform_count / 5.0, 1.0)
        norm_network = min(network_size / 20.0, 1.0)
        financial_factor = 1.0 if has_financials else 0.0

        risk_score = (
            (drug_probability * 0.40) +
            (automation_confidence * 0.15) +
            (norm_platform * 0.15) +
            (norm_network * 0.20) +
            (financial_factor * 0.10)
        )

        # Classify risk level
        if risk_score >= 0.75:
            severity = "CRITICAL"
        elif risk_score >= 0.50:
            severity = "HIGH"
        elif risk_score >= 0.25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "intelligence_risk_score": round(risk_score, 3),
            "severity": severity,
            "indicators": {
                "drug_probability": drug_probability,
                "automation_confidence": automation_confidence,
                "platforms_monitored": platform_count,
                "network_nodes": network_size,
                "financial_traces_found": has_financials
            }
        }

    def prioritize_watchlist(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort a watchlist of targets by risk score descending."""
        scored_targets = []
        for t in targets:
            score_data = self.calculate_risk_score(
                drug_probability=t.get("drug_probability", 0.0),
                automation_confidence=t.get("automation_confidence", 0.0),
                platform_count=t.get("platform_count", 0),
                network_size=t.get("network_size", 0),
                has_financials=t.get("has_financials", False)
            )
            t_copy = dict(t)
            t_copy.update(score_data)
            scored_targets.append(t_copy)

        # Sort by risk score descending
        return sorted(scored_targets, key=lambda x: x["intelligence_risk_score"], reverse=True)
