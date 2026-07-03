from dataclasses import dataclass, field
from rakshastra_core.models.base import RakshastraModel, Severity, Confidence

@dataclass
class Evidence(RakshastraModel):
    tool: str = ""
    host: str = ""
    timestamp: str = ""
    finding: str = ""
    raw_output: str = ""
    severity: Severity = Severity.INFO
    confidence: Confidence = Confidence.TENTATIVE
    tags: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    # Reproducibility fields
    collector_version: str = ""       # Version of the tool/collector that produced this
    command: str = ""                 # Exact command that was executed
    duration: float = 0.0            # Execution duration in seconds
    exit_code: int | None = None     # Process exit code (None if not applicable)
    checksum: str = ""               # SHA-256 of raw_output for integrity verification
    platform: str = ""               # OS/platform where evidence was collected

    @classmethod
    def from_dict(cls, data: dict):
        d = dict(data)
        if "severity" in d and isinstance(d["severity"], str):
            d["severity"] = Severity(d["severity"])
        if "confidence" in d and isinstance(d["confidence"], str):
            d["confidence"] = Confidence(d["confidence"])
        return cls(**d)
