"""Regression harness: load multi-agent fixture families and assert protocol evaluator outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lean_langchain_evals.fixtures import MULTI_AGENT_FAMILIES
from lean_langchain_evals.golden import load_golden_cases
from lean_langchain_policy.pack_loader import load_pack
from lean_langchain_policy.models import PolicyPack
from lean_langchain_policy.protocol_evaluator import (
    evaluate_protocol_obligation,
)

# Pack name per obligation_class when a dedicated pack exists.
OBLIGATION_CLASS_PACK: dict[str, str] = {
    "handoff_legality": "single_owner_handoff_v1",
    "lock_ownership_invariant": "lock_ownership_invariant_v1",
    "evidence_complete_execution_token": "evidence_complete_execution_token_v1",
}


def _make_pack_for_obligation_class(obligation_class: str) -> PolicyPack:
    """Build a minimal PolicyPack with the given obligation class enabled."""
    base = {
        "version": "1",
        "name": "regression",
        "description": "",
    }
    flag = {
        "delegation_admissibility": {"delegation_admissibility": True},
        "state_transition_preservation": {"state_transition_preservation": True},
        "artifact_admissibility": {"artifact_admissibility": True},
        "side_effect_authorization": {"side_effect_authorization": True},
    }.get(obligation_class, {})
    return PolicyPack(**base, **flag)


def test_multi_agent_golden_load_families() -> None:
    """Load multi-agent families; assert at least one case and required fields."""
    cases = load_golden_cases(MULTI_AGENT_FAMILIES[:1])
    assert isinstance(cases, list)
    for c in cases:
        assert c.case_id
        assert isinstance(c.expected_decision, str)


def test_load_all_multi_agent_families() -> None:
    """Load all multi-agent fixture families; assert at least one case per family."""
    cases = load_golden_cases(MULTI_AGENT_FAMILIES)
    assert len(cases) >= len(MULTI_AGENT_FAMILIES)
    for c in cases:
        assert c.case_id
        assert isinstance(c.expected_decision, str)
        assert isinstance(c.expected_terminal_status, str)


def _events_for_handoff(owner_match: bool) -> list[dict]:
    """Build protocol events for handoff_legality: same or different owner."""
    if owner_match:
        return [
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
    return [
        {
            "kind": "claim",
            "event_id": "e1",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "t1", "task_class": "patch"},
        },
        {
            "kind": "delegate",
            "event_id": "e2",
            "actor": {"agent_id": "bob", "role": "other"},
            "task": {"task_id": "t1", "task_class": "patch"},
            "prior_event_ids": ["e1"],
        },
    ]


def test_multi_agent_golden_handoff_good() -> None:
    """handoff_good family: same owner claim+delegate -> accepted."""
    cases = load_golden_cases(["handoff_good"])
    assert len(cases) >= 1
    case = cases[0]
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = _events_for_handoff(owner_match=True)
    result = evaluate_protocol_obligation("handoff_legality", events, pack)
    assert result.decision == case.expected_decision
    assert result.trust_level == case.expected_trust_level


def test_multi_agent_golden_handoff_bad_owner() -> None:
    """handoff_bad_owner family: different owner delegate -> rejected."""
    cases = load_golden_cases(["handoff_bad_owner"])
    assert len(cases) >= 1
    case = cases[0]
    pack = PolicyPack(version="1", name="single_owner", description="", single_owner_handoff=True)
    events = _events_for_handoff(owner_match=False)
    result = evaluate_protocol_obligation("handoff_legality", events, pack)
    assert result.decision == case.expected_decision
    assert result.trust_level == case.expected_trust_level
    assert (
        any(r in result.reasons for r in case.expected_reason_codes)
        or not case.expected_reason_codes
    )


def _events_for_lock_conflict() -> list[dict]:
    """Events that trigger lock_conflict: lock by A then lock by B."""
    return [
        {
            "kind": "lock",
            "event_id": "e1",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "r1", "task_class": "resource"},
        },
        {
            "kind": "lock",
            "event_id": "e2",
            "actor": {"agent_id": "bob", "role": "other"},
            "task": {"task_id": "r1", "task_class": "resource"},
        },
    ]


def test_multi_agent_golden_lock_conflict() -> None:
    """lock_conflict family: second lock while held -> rejected with lock_conflict."""
    cases = load_golden_cases(["lock_conflict"])
    assert len(cases) >= 1
    case = cases[0]
    pack = PolicyPack(version="1", name="lock", description="", lock_ownership_invariant=True)
    events = _events_for_lock_conflict()
    result = evaluate_protocol_obligation("lock_ownership_invariant", events, pack)
    assert result.decision == case.expected_decision
    assert result.trust_level == case.expected_trust_level
    assert any(r in result.reasons for r in case.expected_reason_codes)


def test_regression_fixtures_from_dir_assert_decision_and_trust() -> None:
    """Load structured fixture JSON from tests/regressions/fixtures/ and assert expected decision/trust/reasons."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    if not fixtures_dir.is_dir():
        pytest.skip("fixtures dir not found")
    multi_agent_files = list(fixtures_dir.glob("multi_agent_*.json"))
    if not multi_agent_files:
        pytest.skip("no multi_agent fixture JSON files")
    for path in multi_agent_files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        expected_decision = raw.get("expected_decision", "")
        expected_trust = raw.get("expected_trust_level", "")
        expected_reasons = raw.get("expected_reason_codes", [])
        inp = raw.get("obligation_input", {})
        if "owner_match" in inp:
            events = _events_for_handoff(owner_match=inp["owner_match"])
            pack = PolicyPack(version="1", name="so", description="", single_owner_handoff=True)
            result = evaluate_protocol_obligation("handoff_legality", events, pack)
        elif inp.get("lock_held") and inp.get("conflict"):
            events = _events_for_lock_conflict()
            pack = PolicyPack(
                version="1", name="lock", description="", lock_ownership_invariant=True
            )
            result = evaluate_protocol_obligation("lock_ownership_invariant", events, pack)
        elif "obligation_class" in inp and "events" in inp:
            obligation_class = inp["obligation_class"]
            events = inp["events"]
            pack_name = OBLIGATION_CLASS_PACK.get(obligation_class)
            if pack_name:
                try:
                    pack = load_pack(pack_name)
                except FileNotFoundError:
                    pack = _make_pack_for_obligation_class(obligation_class)
            else:
                pack = _make_pack_for_obligation_class(obligation_class)
            result = evaluate_protocol_obligation(obligation_class, events, pack)
        else:
            continue
        assert result.decision == expected_decision, f"{path.name}: decision"
        assert result.trust_level == expected_trust, f"{path.name}: trust_level"
        if expected_reasons:
            assert any(
                r in result.reasons for r in expected_reasons
            ), f"{path.name}: reasons {result.reasons}"
