from fastapi import HTTPException
from models import (
    ThreatAnalyzeRequest,
    EntityCorrelateRequest,
    ChatAnalyzeRequest,
    OcrAnalyzeRequest,
    ReportGenerateRequest,
    RiskScoreRequest,
    InvestigationStartRequest
)
from services import (
    ThreatService,
    EntityService,
    ChatService,
    OcrService,
    ReportService,
    RiskService,
    InvestigationService
)

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
