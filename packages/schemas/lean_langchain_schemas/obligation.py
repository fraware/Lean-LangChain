from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .common import StrictModel, VersionedRecord
from .environment import EnvironmentFingerprint


class ObligationTarget(StrictModel):
    repo_id: str
    file: str
    declarations: list[str] = Field(default_factory=list)


class ObligationPolicy(StrictModel):
    must_pass_axiom_audit: bool = True
    allow_trust_compiler: bool = False
    require_human_if_imports_change: bool = True
    protected_paths: list[str] = Field(default_factory=list)


class Obligation(VersionedRecord):
    obligation_id: str
    kind: Literal[
        "patch_admissibility",
        "delegation_admissibility",
        "handoff_legality",
        "state_transition_preservation",
        "artifact_admissibility",
        "side_effect_authorization",
        "trust_audit",
        "lock_ownership_invariant",
    ]
    status: Literal["pending", "proved", "refuted", "blocked", "needs_review", "failed"] = "pending"
    target: ObligationTarget
    claim: str
    inputs: dict[str, Any]
    environment_fingerprint: EnvironmentFingerprint
    policy: ObligationPolicy
