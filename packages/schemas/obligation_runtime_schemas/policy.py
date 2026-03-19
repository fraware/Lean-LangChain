from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import StrictModel


class PolicyResolvedRule(StrictModel):
    """One evaluated policy rule for audit trails."""

    rule_id: str
    source_pack: str
    matched: bool
    effect: Literal["none", "needs_review", "rejected", "blocked", "accepted"]
    reason_code: str


class PolicyDecision(StrictModel):
    decision: Literal["accepted", "rejected", "blocked", "needs_review", "lower_trust", "failed"]
    trust_level: Literal["clean", "warning", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    policy_pack_name: str = ""
    policy_pack_version: str = ""
    resolved_rules: list[PolicyResolvedRule] = Field(default_factory=list)


class PolicyAuditTrail(StrictModel):
    """Structured policy provenance for review UI and witnesses."""

    policy_pack_name: str = ""
    policy_pack_version: str = ""
    resolved_rules: list[PolicyResolvedRule] = Field(default_factory=list)
