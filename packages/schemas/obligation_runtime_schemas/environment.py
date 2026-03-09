from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import VersionedRecord
from .hashing import canonical_sha256


class EnvironmentFingerprint(VersionedRecord):
    repo_id: str
    repo_url: str | None = None
    commit_sha: str
    lean_toolchain: str
    lakefile_hash: str
    manifest_hash: str | None = None
    target_platform: str = Field(default="linux/amd64")
    build_flags: list[str] = Field(default_factory=list)
    os_family: Literal["linux", "darwin", "windows"] = "linux"

    def fingerprint_id(self) -> str:
        payload = self.model_dump(mode="json", exclude={"created_at", "schema_version"})
        return canonical_sha256(payload)
