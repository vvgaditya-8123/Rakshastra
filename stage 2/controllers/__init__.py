from fastapi import HTTPException
from models import (
    ThreatAnalyzeRequest,
    EntityCorrelateRequest,
    ChatAnalyzeRequest,
    OcrAnalyzeRequest,
    ReportGenerateRequest,
    RiskScoreRequest,
    InvestigationStartRequest,
    APTAttributionRequest,
    AttackPredictionRequest,
    ThreatIntelSearchRequest,
    SOARIncidentRequest,
    SOARPlaybookExecuteRequest,
    AttackPathRequest,
    BlastRadiusRequest,
    UEBAQueryRequest
)
from services import (
    ThreatService,
    EntityService,
    ChatService,
    OcrService,
    ReportService,
    RiskService,
    InvestigationService,
    APTService,
    ThreatIntelService,
    SOARService,
    AttackGraphService,
    UEBAService
)
from typing import Optional, Dict, Any, List


class ThreatController:
    @staticmethod
    def analyze_text(request: ThreatAnalyzeRequest):
        return ThreatService.analyze_text(
            text=request.text,
            has_image=request.has_image,
            ocr_text=request.ocr_text
        )

class EntityController:
    @staticmethod
    def correlate(request: EntityCorrelateRequest):
        if request.action == "link":
            if not request.entity_a or not request.entity_b:
                raise HTTPException(status_code=400, detail="entity_a and entity_b are required for link action")
            return EntityService.link_entities(request.entity_a, request.entity_b)
        elif request.action == "resolve":
            if not request.seed_entity:
                raise HTTPException(status_code=400, detail="seed_entity is required for resolve action")
            return EntityService.resolve_operator(request.seed_entity)
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'link' or 'resolve'")

class ChatController:
    @staticmethod
    def analyze(request: ChatAnalyzeRequest):
        messages = request.messages
        if not messages:
            if request.message:
                messages = [request.message]
            else:
                raise HTTPException(status_code=400, detail="Either message or messages must be provided")
        return ChatService.analyze_chat(messages)

class OcrController:
    @staticmethod
    def analyze(request: OcrAnalyzeRequest):
        return OcrService.extract_text_from_image(request.image_base64)

class ReportController:
    @staticmethod
    def generate(request: ReportGenerateRequest):
        return ReportService.generate_report(
            title=request.title,
            report_type=request.report_type,
            executive_summary=request.executive_summary,
            findings=request.findings,
            risk_summary=request.risk_summary,
            recommendations=request.recommendations
        )

class RiskController:
    @staticmethod
    def score(request: RiskScoreRequest):
        return RiskService.calculate_risk(
            drug_probability=request.drug_probability,
            automation_confidence=request.automation_confidence,
            platform_count=request.platform_count,
            network_size=request.network_size,
            has_financials=request.has_financials
        )

class InvestigationController:
    @staticmethod
    def start(request: InvestigationStartRequest):
        return InvestigationService.start_investigation(request.session_id)


class APTController:
    @staticmethod
    def attribute(request: APTAttributionRequest):
        return APTService.attribute(
            observed_ttps=request.observed_ttps,
            observed_iocs=request.observed_iocs,
            target_sector=request.target_sector,
            target_country=request.target_country
        )

    @staticmethod
    def predict(request: AttackPredictionRequest):
        return APTService.predict(
            observed_ttps=request.observed_ttps,
            attributed_group_id=request.attributed_group_id
        )

    @staticmethod
    def full_analysis(request: APTAttributionRequest):
        return APTService.full_analysis(
            observed_ttps=request.observed_ttps,
            observed_iocs=request.observed_iocs,
            target_sector=request.target_sector,
            target_country=request.target_country,
            org_assets=request.org_assets,
            create_incident=request.create_incident
        )

    @staticmethod
    def get_techniques(tactic_id: Optional[str] = None):
        return APTService.get_mitre_techniques(tactic_id)

    @staticmethod
    def get_groups():
        return APTService.get_mitre_groups()

    @staticmethod
    def get_tactics():
        return APTService.get_mitre_tactics()

    @staticmethod
    def get_group_profile(group_id: str):
        return APTService.get_group_profile(group_id)


class ThreatIntelController:
    @staticmethod
    def search(request: ThreatIntelSearchRequest):
        return ThreatIntelService.search(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k
        )


class SOARController:
    @staticmethod
    def create_incident(request: SOARIncidentRequest):
        return SOARService.create_incident(
            alert_data=request.alert_data,
            severity=request.severity,
            attribution_result=request.attribution_result,
            title=request.title,
            mode=request.mode
        )

    @staticmethod
    def execute_playbook(request: SOARPlaybookExecuteRequest):
        return SOARService.execute_playbook(
            incident_id=request.incident_id,
            mode=request.mode
        )

    @staticmethod
    def get_playbooks():
        return SOARService.get_playbooks()

    @staticmethod
    def get_incidents(status: Optional[str] = None, limit: int = 50):
        return SOARService.get_incidents(status, limit)

    @staticmethod
    def get_incident(incident_id: str):
        return SOARService.get_incident(incident_id)

    @staticmethod
    def get_actions(incident_id: str):
        return SOARService.get_actions(incident_id)


class AttackGraphController:
    @staticmethod
    def compute_paths(request: AttackPathRequest):
        return AttackGraphService.compute_paths(
            entry_point_id=request.entry_point_id,
            target_id=request.target_id,
            max_depth=request.max_depth
        )

    @staticmethod
    def simulate_blast_radius(request: BlastRadiusRequest):
        return AttackGraphService.simulate_blast_radius(
            compromised_asset_id=request.compromised_asset_id
        )

    @staticmethod
    def get_chokepoints():
        return AttackGraphService.get_chokepoints()


class UEBAController:
    @staticmethod
    def get_anomalies(request: UEBAQueryRequest):
        return UEBAService.get_anomalies(
            entity_id=request.entity_id,
            category=request.category,
            severity=request.severity,
            since=request.since,
            limit=request.limit
        )

    @staticmethod
    def get_apt_patterns(entity_id: str):
        return UEBAService.get_apt_patterns(entity_id)

    @staticmethod
    def get_risk_timeline(entity_id: str):
        return UEBAService.get_risk_timeline(entity_id)

