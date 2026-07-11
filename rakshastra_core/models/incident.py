from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel, Severity

@dataclass
class Incident(RakshastraModel):
    title: str = ""
    description: str = ""
    severity: Severity = Severity.INFO
    status: str = "open"
    evidence_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    containment_actions: list[str] = field(default_factory=list)
    remediation_steps: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        d = dict(data)
        if "severity" in d and isinstance(d["severity"], str):
            d["severity"] = Severity(d["severity"])
        return cls(**d)
