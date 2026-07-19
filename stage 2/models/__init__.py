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

# APT Attribution
class APTAttributionRequest(BaseModel):
    observed_ttps: List[str]
    observed_iocs: Optional[List[str]] = []
    target_sector: Optional[str] = None
    target_country: Optional[str] = None
    org_assets: Optional[List[Dict[str, Any]]] = []
    create_incident: bool = True

# Attack Prediction
class AttackPredictionRequest(BaseModel):
    observed_ttps: List[str]
    attributed_group_id: Optional[str] = None
    top_k: int = 10

# Threat Intel Search
class ThreatIntelSearchRequest(BaseModel):
    query: str
    search_type: str = "general"  # general, cve, apt_group, source_type
    top_k: int = 10

# SOAR Incident
class SOARIncidentRequest(BaseModel):
    alert_data: Dict[str, Any] = {}
    severity: str = "HIGH"
    attribution_result: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    mode: str = "simulate"  # simulate, approve, auto_execute

# SOAR Playbook Execution
class SOARPlaybookExecuteRequest(BaseModel):
    incident_id: str
    mode: str = "simulate"

# Attack Path
class AttackPathRequest(BaseModel):
    entry_point_id: str
    target_id: str
    max_depth: int = 8

# Blast Radius
class BlastRadiusRequest(BaseModel):
    compromised_asset_id: str

# UEBA Query
class UEBAQueryRequest(BaseModel):
    entity_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    since: Optional[str] = None
    limit: int = 50
