from __future__ import annotations

from typing import Literal

from pydantic import Field

from lean_langchain_schemas.common import StrictModel


class TrustGateRule(StrictModel):
    """Require human review when batch trust level matches and optional path globs match."""

    rule_id: str = "trust_gate"
    when_trust_level: list[Literal["clean", "warning", "blocked"]] = Field(default_factory=list)
    path_globs: list[str] = Field(default_factory=list)
    require_human: bool = True
    reason_code: str = "trust_gate_review"


class PathRule(StrictModel):
    """Optional per-path review gate: if a changed file matches glob, require human review."""

    glob: str
    require_human: bool = True
    reason_code: str = "path_rule_review"


class PolicyPack(StrictModel):
    version: str
    name: str
    description: str
    allow_trust_compiler: bool = False
    block_sorry_ax: bool = True
    block_unexpected_custom_axioms: bool = True
    require_human_if_imports_change: bool = True
    protected_paths: list[str] = Field(default_factory=list)
    path_rules: list[PathRule] = Field(default_factory=list)
    trust_gates: list[TrustGateRule] = Field(default_factory=list)
    require_human_on_trust_delta: bool = True
    allow_interactive_warnings: bool = True
    # V2 protocol packs
    single_owner_handoff: bool = False
    reviewer_gated_execution: bool = False
    lock_ownership_invariant: bool = False
    evidence_complete_execution_token: bool = False
    delegation_admissibility: bool = False
    state_transition_preservation: bool = False
    artifact_admissibility: bool = False
    side_effect_authorization: bool = False
    composition_conflict_policy: Literal["last_wins", "error_on_import_scalar_override"] = (
        "last_wins"
    )
