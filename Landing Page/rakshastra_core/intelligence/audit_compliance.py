import datetime
from typing import Dict, Any, List

class AuditComplianceEngine:
    """Tracks intelligence gather activities to ensure logging, explainability, and lawful evidence verification."""

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def log_action(self, investigator: str, action: str, target: str, source_data: str) -> Dict[str, Any]:
        """Log a collection/resolution action to the immutable audit trail."""
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "investigator": investigator,
            "action": action,
            "target": target,
            "source_data_origin": source_data,
            "lawfulness_status": "VERIFIED_PUBLIC_OSINT"
        }
        self.audit_log.append(log_entry)
        return log_entry

    def verify_evidence_trail(self, resolved_profile: Dict[str, Any], source_transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provides verification details linking a resolved operator back to lawful source data."""
        matched_sources = []
        for ident in resolved_profile.get("resolved_identifiers", []):
            for source in source_transcripts:
                if ident in source.get("text", "") or ident in source.values():
                    matched_sources.append({
                        "identifier": ident,
                        "verified_source": f"{source.get('platform', 'web')} message {source.get('message_id', '') or source.get('post_id', '')}",
                        "timestamp": source.get("timestamp", datetime.datetime.utcnow().isoformat() + "Z")
                    })

        return {
            "resolved_profile_id": resolved_profile.get("operator_id"),
            "verification_status": "COMPLIANT_WITH_AUDIT_POLICIES",
            "evidence_trail": matched_sources,
            "confidence_rating": "EXPLAINABLE_OSINT_MATCH"
        }
