from dataclasses import dataclass, field
from enum import Enum
from rakshastra_core.models.base import RakshastraModel

class AssetType(str, Enum):
    HOST = "host"
    CONTAINER = "container"
    SERVICE = "service"
    USER = "user"
    NETWORK = "network"
    SECRET = "secret"
    DATABASE = "database"
    FIREWALL = "firewall"
    CLOUD_RESOURCE = "cloud_resource"
    VULNERABILITY = "cve"
    INCIDENT = "incident"
    EVIDENCE = "evidence"
    REPORT = "report"
    VPN = "vpn"

@dataclass
class Asset(RakshastraModel):
    name: str = ""
    asset_type: AssetType = AssetType.HOST
    hostname: str | None = None
    ip_address: str | None = None
    properties: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        d = dict(data)
        if "asset_type" in d and isinstance(d["asset_type"], str):
            d["asset_type"] = AssetType(d["asset_type"])
        return cls(**d)

@dataclass
class AssetRelation(RakshastraModel):
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    properties: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
