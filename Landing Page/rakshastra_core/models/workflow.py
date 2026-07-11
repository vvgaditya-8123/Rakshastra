from enum import Enum
from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel

class WorkflowState(str, Enum):
    RECON = "Recon"
    ENUMERATION = "Enumeration"
    COLLECTION = "Collection"
    EVIDENCE = "Evidence"
    ANALYSIS = "Analysis"
    PRIORITIZATION = "Prioritization"
    RECOMMENDATION = "Recommendation"
    VERIFICATION = "Verification"
    REPORT = "Report"

@dataclass
class WorkflowStep(RakshastraModel):
    session_id: str = ""
    phase: WorkflowState = WorkflowState.RECON
    command: str = ""
    status: str = "completed"  # "completed", "failed", "skipped"
    duration: float = 0.0
    output_summary: str = ""

    @classmethod
    def from_dict(cls, data: dict):
        d = dict(data)
        if "phase" in d and isinstance(d["phase"], str):
            d["phase"] = WorkflowState(d["phase"])
        return cls(**d)
