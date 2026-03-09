from __future__ import annotations

from pydantic import Field

from .common import VersionedRecord
from .environment import EnvironmentFingerprint
from .interactive import InteractiveCheckResult
from .policy import PolicyDecision


class WitnessBundle(VersionedRecord):
    bundle_id: str
    obligation_id: str
    environment_fingerprint: EnvironmentFingerprint
    interactive: InteractiveCheckResult
    acceptance: dict = Field(default_factory=dict)
    policy: PolicyDecision
    approval: dict = Field(default_factory=dict)
    trace: dict = Field(default_factory=dict)
