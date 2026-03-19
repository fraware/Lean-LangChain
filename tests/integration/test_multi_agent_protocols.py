"""Integration tests: multi-agent protocol evaluation (handoff, delegation)."""

from __future__ import annotations

from lean_langchain_policy.models import PolicyPack
from lean_langchain_policy.protocol_evaluator import evaluate_protocol_obligation


def test_multi_agent_protocols_handoff_legality_same_owner_accepted() -> None:
    """Same owner claim + delegate -> handoff_legality accepted."""
    pack = PolicyPack(
        version="1",
        name="single_owner",
        description="",
        single_owner_handoff=True,
    )
    events = [
        {
            "kind": "claim",
            "event_id": "e1",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "t1", "task_class": "patch"},
        },
        {
            "kind": "delegate",
            "event_id": "e2",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "t1", "task_class": "patch"},
            "prior_event_ids": ["e1"],
        },
    ]
    result = evaluate_protocol_obligation("handoff_legality", events, pack)
    assert result.decision == "accepted"
    assert result.trust_level in ("clean", "warning")
