from __future__ import annotations

from pydantic import Field

from obligation_runtime_schemas.common import StrictModel


class PolicyPack(StrictModel):
    version: str
    name: str
    description: str
    allow_trust_compiler: bool = False
    block_sorry_ax: bool = True
    block_unexpected_custom_axioms: bool = True
    require_human_if_imports_change: bool = True
    protected_paths: list[str] = Field(default_factory=list)
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
