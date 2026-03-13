from __future__ import annotations

from pydantic import Field

from .common import VersionedRecord
from .environment import EnvironmentFingerprint
from .interactive import InteractiveCheckResult
from .policy import PolicyDecision


class AcceptanceSummary(VersionedRecord):
    """Typed summary of batch (acceptance lane) verification for WitnessBundle.acceptance."""

    ok: bool = True
    trust_level: str = "clean"
    reasons: list[str] = Field(default_factory=list)
    build: dict = Field(default_factory=dict)
    axiom_audit: dict = Field(default_factory=dict)
    fresh_checker: dict = Field(default_factory=dict)


class WitnessBundle(VersionedRecord):
    bundle_id: str
    obligation_id: str
    environment_fingerprint: EnvironmentFingerprint
    interactive: InteractiveCheckResult
    # Acceptance lane result; dict for flexibility, typically matches AcceptanceSummary/BatchVerifyResult shape.
    acceptance: dict = Field(default_factory=dict)
    policy: PolicyDecision
    approval: dict = Field(default_factory=dict)
    trace: dict = Field(default_factory=dict)
