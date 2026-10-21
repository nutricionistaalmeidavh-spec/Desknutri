from __future__ import annotations
from dataclasses import dataclass,asdict

# Release build for 6.5.5 (CHANGELOG.md synchronized).
APP_VERSION = "6.5.5"
SCHEMA_VERSION = 15
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