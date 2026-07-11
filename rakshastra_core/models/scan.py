from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel

@dataclass
class Scan(RakshastraModel):
    scan_type: str = ""
    target: str = ""
    status: str = "pending"
    started_at: str = ""
    completed_at: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
