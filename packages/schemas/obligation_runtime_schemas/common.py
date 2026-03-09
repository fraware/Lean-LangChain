from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=False)


class VersionedRecord(StrictModel):
    schema_version: str = Field(default="0.1.0")
    created_at: datetime = Field(default_factory=utc_now)
