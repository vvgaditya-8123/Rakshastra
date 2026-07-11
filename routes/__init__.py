from fastapi import APIRouter
from models import (
    ThreatAnalyzeRequest,
    EntityCorrelateRequest,
    ChatAnalyzeRequest,
    OcrAnalyzeRequest,
    ReportGenerateRequest,
    RiskScoreRequest,
    InvestigationStartRequest
)
from controllers import (
    ThreatController,
    EntityController,
    ChatController,
    OcrController,
    ReportController,
    RiskController,
    InvestigationController
)

router = APIRouter()

@router.post("/threat/analyze-text")
def analyze_text(request: ThreatAnalyzeRequest):
    return ThreatController.analyze_text(request)

@router.post("/entity/correlate")
def correlate(request: EntityCorrelateRequest):
    return EntityController.correlate(request)

@router.post("/chat/analyze")
def analyze_chat(request: ChatAnalyzeRequest):
    return ChatController.analyze(request)

@router.post("/ocr/analyze")
def ocr_analyze(request: OcrAnalyzeRequest):
    return OcrController.analyze(request)

@router.post("/report/generate")
def generate_report(request: ReportGenerateRequest):
    return ReportController.generate(request)

@router.post("/risk/score")
def risk_score(request: RiskScoreRequest):
    return RiskController.score(request)

@router.post("/investigation/start")
def start_investigation(request: InvestigationStartRequest):
    return InvestigationController.start(request)

@router.get("/status")
def get_status():
    # Simple status endpoint returning nominal service status
    return {
        "status": "NOMINAL",
        "api_version": "v1",
        "service": "Rakshastra API"
    }
