"""Unit tests for V2 protocol evaluator (handoff_legality, reviewer_gated, lock, and V2 classes)."""

from __future__ import annotations

from obligation_runtime_policy.constants import (
    REASON_ARTIFACT_NOT_ADMISSIBLE,
    REASON_DELEGATE_WITHOUT_PRIOR_CLAIM,
    REASON_EVIDENCE_INCOMPLETE,
    REASON_INVALID_STATE_TRANSITION,
    REASON_LOCK_CONFLICT,
    REASON_MISSING_APPROVAL_TOKEN,
    REASON_RELEASE_WITHOUT_LOCK,
    REASON_SIDE_EFFECT_UNAUTHORIZED,
)
from obligation_runtime_policy.models import PolicyPack
from obligation_runtime_policy.protocol_evaluator import (
    evaluate_artifact_admissibility,
    evaluate_delegation_admissibility,
    evaluate_evidence_complete_execution_token,
    evaluate_handoff_legality,
    evaluate_lock_ownership_invariant,
    evaluate_protocol_obligation,
    evaluate_reviewer_gated,
    evaluate_side_effect_authorization,
    evaluate_state_transition_preservation,
)


def test_handoff_good_single_owner() -> None:
    """Claim then delegate from same owner -> accepted."""
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
        {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
    ]
    result = evaluate_handoff_legality(events, pack)
    assert result.decision == "accepted"
    assert result.trust_level == "clean"


def test_handoff_bad_owner_rejected() -> None:
    """Delegate from different owner -> rejected."""
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
        {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "bob", "role": "other"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
    ]
    result = evaluate_handoff_legality(events, pack)
    assert result.decision == "rejected"
    assert "owner_mismatch" in result.reasons


def test_handoff_delegate_without_claim_rejected() -> None:
    """Delegate without prior claim -> rejected."""
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = [
        {"kind": "delegate", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
    ]
    result = evaluate_handoff_legality(events, pack)
    assert result.decision == "rejected"
    assert REASON_DELEGATE_WITHOUT_PRIOR_CLAIM in result.reasons


def test_evaluate_protocol_obligation_handoff_legality() -> None:
    """evaluate_protocol_obligation dispatches handoff_legality to handoff evaluator."""
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
        {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
    ]
    result = evaluate_protocol_obligation("handoff_legality", events, pack)
    assert result.decision == "accepted"


def test_reviewer_gated_without_approve_blocked() -> None:
    """reviewer_gated with no approve event returns blocked."""
    pack = PolicyPack(version="1", name="rg", description="", reviewer_gated_execution=True)
    events = [{"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}}]
    result = evaluate_reviewer_gated(events, pack)
    assert result.decision == "blocked"
    assert REASON_MISSING_APPROVAL_TOKEN in result.reasons


def test_reviewer_gated_with_approve_accepted() -> None:
    """reviewer_gated with approve event returns accepted."""
    pack = PolicyPack(version="1", name="rg", description="", reviewer_gated_execution=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
        {"kind": "approve", "event_id": "e2", "actor": {"agent_id": "reviewer", "role": "reviewer"}, "task": {"task_id": "t1", "task_class": "patch"}},
    ]
    result = evaluate_reviewer_gated(events, pack)
    assert result.decision == "accepted"


def test_evaluate_protocol_obligation_reviewer_gated() -> None:
    """evaluate_protocol_obligation dispatches reviewer_gated to reviewer_gated evaluator."""
    pack = PolicyPack(version="1", name="rg", description="", reviewer_gated_execution=True)
    events = [{"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}}]
    result = evaluate_protocol_obligation("reviewer_gated", events, pack)
    assert result.decision == "blocked"


def test_lock_ownership_invariant_lock_then_release_accepted() -> None:
    """lock by A then release by A -> accepted."""
    pack = PolicyPack(version="1", name="lock", description="", lock_ownership_invariant=True)
    events = [
        {"kind": "lock", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}},
        {"kind": "release", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}},
    ]
    result = evaluate_lock_ownership_invariant(events, pack)
    assert result.decision == "accepted"


def test_lock_ownership_invariant_conflict_rejected() -> None:
    """lock by A then lock by B without release -> lock_conflict."""
    pack = PolicyPack(version="1", name="lock", description="", lock_ownership_invariant=True)
    events = [
        {"kind": "lock", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}},
        {"kind": "lock", "event_id": "e2", "actor": {"agent_id": "bob", "role": "other"}, "task": {"task_id": "t1", "task_class": "resource"}},
    ]
    result = evaluate_lock_ownership_invariant(events, pack)
    assert result.decision == "rejected"
    assert REASON_LOCK_CONFLICT in result.reasons


def test_lock_ownership_invariant_release_without_lock_rejected() -> None:
    """release without prior lock -> release_without_lock."""
    pack = PolicyPack(version="1", name="lock", description="", lock_ownership_invariant=True)
    events = [{"kind": "release", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}}]
    result = evaluate_lock_ownership_invariant(events, pack)
    assert result.decision == "rejected"
    assert REASON_RELEASE_WITHOUT_LOCK in result.reasons


def test_evaluate_protocol_obligation_lock_ownership_invariant() -> None:
    """evaluate_protocol_obligation dispatches lock_ownership_invariant."""
    pack = PolicyPack(version="1", name="lock", description="", lock_ownership_invariant=True)
    events = [
        {"kind": "lock", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}},
        {"kind": "release", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "resource"}},
    ]
    result = evaluate_protocol_obligation("lock_ownership_invariant", events, pack)
    assert result.decision == "accepted"


def test_delegation_admissibility_good_accepted() -> None:
    """Claim then delegate same owner same task -> accepted."""
    pack = PolicyPack(version="1", name="d", description="", delegation_admissibility=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
        {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
    ]
    result = evaluate_delegation_admissibility(events, pack)
    assert result.decision == "accepted"


def test_delegation_admissibility_delegate_without_claim_rejected() -> None:
    """Delegate without prior claim -> rejected."""
    pack = PolicyPack(version="1", name="d", description="", delegation_admissibility=True)
    events = [{"kind": "delegate", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}}]
    result = evaluate_delegation_admissibility(events, pack)
    assert result.decision == "rejected"
    assert REASON_DELEGATE_WITHOUT_PRIOR_CLAIM in result.reasons


def test_state_transition_preservation_execute_after_approve_accepted() -> None:
    """Execute after approve -> accepted."""
    pack = PolicyPack(version="1", name="s", description="", state_transition_preservation=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {}, "task": {}},
        {"kind": "approve", "event_id": "e2", "actor": {}, "task": {}},
        {"kind": "execute", "event_id": "e3", "actor": {}, "task": {}},
    ]
    result = evaluate_state_transition_preservation(events, pack)
    assert result.decision == "accepted"


def test_state_transition_preservation_execute_before_approve_rejected() -> None:
    """Execute before approve -> invalid_state_transition."""
    pack = PolicyPack(version="1", name="s", description="", state_transition_preservation=True)
    events = [
        {"kind": "claim", "event_id": "e1", "actor": {}, "task": {}},
        {"kind": "execute", "event_id": "e2", "actor": {}, "task": {}},
    ]
    result = evaluate_state_transition_preservation(events, pack)
    assert result.decision == "rejected"
    assert REASON_INVALID_STATE_TRANSITION in result.reasons


def test_artifact_admissibility_approve_with_artifact_accepted() -> None:
    """Approve event with artifacts payload -> accepted."""
    pack = PolicyPack(version="1", name="a", description="", artifact_admissibility=True)
    events = [{"kind": "approve", "event_id": "e1", "actor": {}, "task": {}, "payload": {"artifacts": [{}]}}]
    result = evaluate_artifact_admissibility(events, pack)
    assert result.decision == "accepted"


def test_artifact_admissibility_claim_with_artifact_rejected() -> None:
    """Claim event with artifacts -> artifact_not_admissible."""
    pack = PolicyPack(version="1", name="a", description="", artifact_admissibility=True)
    events = [{"kind": "claim", "event_id": "e1", "actor": {}, "task": {}, "payload": {"artifacts": [{}]}}]
    result = evaluate_artifact_admissibility(events, pack)
    assert result.decision == "rejected"
    assert REASON_ARTIFACT_NOT_ADMISSIBLE in result.reasons


def test_side_effect_authorization_execute_after_approve_accepted() -> None:
    """Execute after approve -> accepted."""
    pack = PolicyPack(version="1", name="s", description="", side_effect_authorization=True)
    events = [
        {"kind": "approve", "event_id": "e1", "actor": {}, "task": {}},
        {"kind": "execute", "event_id": "e2", "actor": {}, "task": {}},
    ]
    result = evaluate_side_effect_authorization(events, pack)
    assert result.decision == "accepted"


def test_side_effect_authorization_execute_before_approve_rejected() -> None:
    """Execute without prior approve -> side_effect_unauthorized."""
    pack = PolicyPack(version="1", name="s", description="", side_effect_authorization=True)
    events = [{"kind": "execute", "event_id": "e1", "actor": {}, "task": {}}]
    result = evaluate_side_effect_authorization(events, pack)
    assert result.decision == "rejected"
    assert REASON_SIDE_EFFECT_UNAUTHORIZED in result.reasons


def test_evidence_complete_execution_token_with_token_accepted() -> None:
    """Event with evidence_complete in payload -> accepted."""
    pack = PolicyPack(version="1", name="e", description="", evidence_complete_execution_token=True)
    events = [{"kind": "execute", "event_id": "e1", "actor": {}, "task": {}, "payload": {"evidence_complete": True}}]
    result = evaluate_evidence_complete_execution_token(events, pack)
    assert result.decision == "accepted"


def test_evidence_complete_execution_token_without_token_blocked() -> None:
    """Pack requires evidence_complete; events lack it -> blocked."""
    pack = PolicyPack(version="1", name="e", description="", evidence_complete_execution_token=True)
    events = [{"kind": "claim", "event_id": "e1", "actor": {}, "task": {}}, {"kind": "execute", "event_id": "e2", "actor": {}, "task": {}}]
    result = evaluate_evidence_complete_execution_token(events, pack)
    assert result.decision == "blocked"
    assert REASON_EVIDENCE_INCOMPLETE in result.reasons
