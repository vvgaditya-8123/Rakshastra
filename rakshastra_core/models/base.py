from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class Confidence(str, Enum):
    CONFIRMED = "CONFIRMED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TENTATIVE = "TENTATIVE"

@dataclass
class RakshastraModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        def serialize_val(val):
            if isinstance(val, Enum):
                return val.value
            elif isinstance(val, list):
                return [serialize_val(x) for x in val]
            elif isinstance(val, dict):
                return {k: serialize_val(v) for k, v in val.items()}
            elif hasattr(val, "to_dict"):
                return val.to_dict()
            return val
        
        result = {}
        for key, val in self.__dict__.items():
            result[key] = serialize_val(val)
        return result

    @classmethod
    def from_dict(cls, data: dict):
        # Base implementation, subclasses can override for nested serialization
        return cls(**data)
