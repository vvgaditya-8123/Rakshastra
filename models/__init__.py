from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Threat Analyze-Text
class ThreatAnalyzeRequest(BaseModel):
    text: str
    has_image: bool = False
    ocr_text: str = ""

# Entity Correlate
class EntityCorrelateRequest(BaseModel):
    action: str  # "link" or "resolve"
    entity_a: Optional[str] = None
    entity_b: Optional[str] = None
    seed_entity: Optional[str] = None

# Chat Analyze
class ChatAnalyzeRequest(BaseModel):
    messages: Optional[List[str]] = None
    message: Optional[str] = None

# OCR Analyze
class OcrAnalyzeRequest(BaseModel):
    image_base64: Optional[str] = None

# Report Generate
class ReportGenerateRequest(BaseModel):
    title: str
    report_type: str
    executive_summary: Optional[str] = ""
    findings: Optional[List[Dict[str, Any]]] = []
    risk_summary: Optional[Dict[str, Any]] = {}
    recommendations: Optional[List[str]] = []

# Risk Score
class RiskScoreRequest(BaseModel):
    drug_probability: float
    automation_confidence: float
    platform_count: int
    network_size: int
    has_financials: bool

# Investigation Start
class InvestigationStartRequest(BaseModel):
    session_id: Optional[str] = None
