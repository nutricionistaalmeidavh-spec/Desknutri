from __future__ import annotations
from dataclasses import dataclass,asdict

APP_VERSION = "6.0.0"
SCHEMA_VERSION = 13
CLINICAL_CONTENT_VERSION = "2026.08"
WHO_ENGINE_VERSION = "pygrowthstandards-0.1.3"
RELEASE_CHANNEL = "stable"

@dataclass(frozen=True)
class VersionInfo:
    app:str=APP_VERSION
    schema:int=SCHEMA_VERSION
    clinical:str=CLINICAL_CONTENT_VERSION
    who:str=WHO_ENGINE_VERSION
    channel:str=RELEASE_CHANNEL
    def as_dict(self):return asdict(self)

VERSION_INFO=VersionInfo()
