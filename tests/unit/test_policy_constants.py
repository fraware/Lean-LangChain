"""Unit tests for canonical policy constants (reason codes, decisions, trust levels)."""

from __future__ import annotations

from lean_langchain_policy.constants import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    DECISION_ACCEPTED,
    DECISION_BLOCKED,
    DECISION_NEEDS_REVIEW,
    DECISION_REJECTED,
    REASON_DELEGATE_WITHOUT_PRIOR_CLAIM,
    REASON_LOCK_CONFLICT,
    REASON_MISSING_APPROVAL_TOKEN,
    REASON_OWNER_MISMATCH,
    REASON_RELEASE_WITHOUT_LOCK,
    TRUST_BLOCKED,
    TRUST_CLEAN,
    TRUST_WARNING,
)


def test_reason_codes_are_non_empty_strings() -> None:
    """All reason constants are non-empty strings for use in policy_decision.reasons."""
    reasons = [
        REASON_DELEGATE_WITHOUT_PRIOR_CLAIM,
        REASON_OWNER_MISMATCH,
        REASON_MISSING_APPROVAL_TOKEN,
        REASON_LOCK_CONFLICT,
        REASON_RELEASE_WITHOUT_LOCK,
    ]
    for r in reasons:
        assert isinstance(r, str), r
        assert len(r) > 0, r


def test_decision_constants_match_schema_literals() -> None:
    """Decision constants align with PolicyDecision.decision literal."""
    assert DECISION_ACCEPTED == "accepted"
    assert DECISION_REJECTED == "rejected"
    assert DECISION_BLOCKED == "blocked"
    assert DECISION_NEEDS_REVIEW == "needs_review"


def test_trust_level_constants() -> None:
    """Trust level constants align with PolicyDecision.trust_level."""
    assert TRUST_CLEAN == "clean"
    assert TRUST_WARNING == "warning"
    assert TRUST_BLOCKED == "blocked"


def test_approval_constants() -> None:
    """Approval token values for state.approval_decision."""
    assert APPROVAL_APPROVED == "approved"
    assert APPROVAL_REJECTED == "rejected"
    assert APPROVAL_PENDING == "pending"
