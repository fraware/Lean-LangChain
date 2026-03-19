"""Canonical policy reason codes and decision values.

Use these constants everywhere (evaluators, graph, tests, docs) so reason codes
and terminal decisions are consistent and discoverable.
"""

from __future__ import annotations

from typing import Literal

# --- Reason codes (policy_decision.reasons) ---
REASON_DELEGATE_WITHOUT_PRIOR_CLAIM = "delegate_without_prior_claim"
REASON_OWNER_MISMATCH = "owner_mismatch"
REASON_MISSING_APPROVAL_TOKEN = "missing_approval_token"
REASON_LOCK_CONFLICT = "lock_conflict"
REASON_RELEASE_WITHOUT_LOCK = "release_without_lock"
REASON_INVALID_STATE_TRANSITION = "invalid_state_transition"
REASON_ARTIFACT_NOT_ADMISSIBLE = "artifact_not_admissible"
REASON_SIDE_EFFECT_UNAUTHORIZED = "side_effect_unauthorized"
REASON_EVIDENCE_INCOMPLETE = "evidence_incomplete"

# --- Terminal decisions (policy_decision.decision) ---
DecisionLiteral = Literal[
    "accepted", "rejected", "blocked", "needs_review", "lower_trust", "failed"
]
DECISION_ACCEPTED: DecisionLiteral = "accepted"
DECISION_REJECTED: DecisionLiteral = "rejected"
DECISION_BLOCKED: DecisionLiteral = "blocked"
DECISION_NEEDS_REVIEW: DecisionLiteral = "needs_review"
DECISION_FAILED: DecisionLiteral = "failed"

# --- Trust levels ---
TrustLiteral = Literal["clean", "warning", "blocked"]
TRUST_CLEAN: TrustLiteral = "clean"
TRUST_WARNING: TrustLiteral = "warning"
TRUST_BLOCKED: TrustLiteral = "blocked"

# --- Approval token values (state.approval_decision) ---
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_PENDING = "pending"
