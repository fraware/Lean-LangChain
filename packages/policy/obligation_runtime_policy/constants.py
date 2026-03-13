"""Canonical policy reason codes and decision values.

Use these constants everywhere (evaluators, graph, tests, docs) so reason codes
and terminal decisions are consistent and discoverable.
"""

from __future__ import annotations

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
DECISION_ACCEPTED = "accepted"
DECISION_REJECTED = "rejected"
DECISION_BLOCKED = "blocked"
DECISION_NEEDS_REVIEW = "needs_review"
DECISION_FAILED = "failed"

# --- Trust levels ---
TRUST_CLEAN = "clean"
TRUST_WARNING = "warning"
TRUST_BLOCKED = "blocked"

# --- Approval token values (state.approval_decision) ---
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_PENDING = "pending"
