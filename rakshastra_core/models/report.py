from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel

@dataclass
class Report(RakshastraModel):
    title: str = ""
    report_type: str = ""
    executive_summary: str = ""
    findings: list[dict] = field(default_factory=list)
    risk_summary: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    generated_at: str = ""

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
