from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fingerprint_id: str
    base_path: Path
    metadata_path: Path


class OverlayRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    fingerprint_id: str
    overlay_path: Path
    metadata_path: Path
