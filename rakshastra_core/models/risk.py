from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel, Severity

@dataclass
class Risk(RakshastraModel):
    title: str = ""
    description: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    # Six-factor risk scoring
    likelihood: float = 0.0            # Probability of exploitation (0.0–1.0)
    impact: float = 0.0               # Damage if exploited (0.0–1.0)
    exploitability: float = 0.5        # How easy to exploit (0.0–1.0)
    exposure: float = 0.5             # How exposed the target is (0.0–1.0)
    business_criticality: float = 0.5  # Business importance of the asset (0.0–1.0)
    internet_exposure: float = 0.0     # Reachable from the internet (0.0–1.0)
    risk_score: float = 0.0           # Composite score (computed)
    severity: Severity = Severity.INFO
    recommended_actions: list[str] = field(default_factory=list)
    attack_path: list[str] = field(default_factory=list)
    mitre_tactics: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        d = dict(data)
        if "severity" in d and isinstance(d["severity"], str):
            d["severity"] = Severity(d["severity"])
        return cls(**d)
