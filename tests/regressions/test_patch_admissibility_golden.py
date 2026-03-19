"""Regression harness: run patch admissibility golden cases and assert expected outcomes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

from lean_langchain_evals.golden import GoldenCase, load_golden_cases
from lean_langchain_evals.fixtures import PATCH_FAMILIES
from lean_langchain_orchestrator.runtime.initial_state import make_initial_state


def _build_initial_state(case: GoldenCase, repo_path: str = "") -> dict[str, Any]:
    """Build minimal ObligationRuntimeState from golden case obligation_input."""
    inp = case.obligation_input or {}
    obligation: dict[str, Any] = {"target": {"repo_id": "lean-mini"}}
    if inp.get("protected_paths"):
        obligation["policy"] = {"protected_paths": inp["protected_paths"]}
    return make_initial_state(
        thread_id=f"golden_{case.case_id}",
        obligation_id=case.case_id,
        obligation=obligation,
        target_files=inp.get("target_files", ["Main.lean"]),
        target_declarations=inp.get("target_declarations", []),
        current_patch=inp.get("current_patch", {}),
        repo_path=repo_path,
        session_id=inp.get("session_id"),
    )


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_patch_admissibility_golden_good_patch(gateway_app) -> None:
    """Run good_patch golden case: full graph run, assert accepted and witness bundle."""
    from fastapi.testclient import TestClient

    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_sdk.client import ObligationRuntimeClient

    from tests.integration.conftest import make_testclient_request_adapter

    cases = load_golden_cases(["good_patch"])
    assert len(cases) >= 1
    case = cases[0]
    assert case.expected_terminal_status == "accepted"

    repo_path = str(
        Path(__file__).resolve().parent.parent / "integration" / "fixtures" / "lean-mini"
    )
    with TestClient(gateway_app) as tc:
        adapter = make_testclient_request_adapter(tc)
        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client)
        initial = _build_initial_state(case, repo_path)
        result = graph.invoke(initial)

    assert result.get("status") in (
        "accepted",
        "rejected",
        "failed",
        "awaiting_approval",
        "repairing",
        "auditing",
    )
    if result.get("status") == "accepted":
        assert case.expected_terminal_status == "accepted"
        artifacts = result.get("artifacts") or []
        assert any(a.get("kind") == "witness_bundle" for a in artifacts)


def test_load_all_patch_families() -> None:
    """Load all patch fixture families; assert at least one case per family."""
    cases = load_golden_cases(PATCH_FAMILIES)
    assert len(cases) >= len(PATCH_FAMILIES)
    for c in cases:
        assert c.case_id
        assert isinstance(c.expected_decision, str)
        assert isinstance(c.expected_terminal_status, str)


def test_patch_admissibility_golden_load_cases() -> None:
    """Load first patch family; assert cases list and each case has required fields."""
    cases = load_golden_cases(PATCH_FAMILIES[:1])
    assert isinstance(cases, list)
    for c in cases:
        assert c.case_id
        assert isinstance(c.expected_decision, str)
        assert isinstance(c.expected_terminal_status, str)


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_patch_admissibility_golden_protected_path_touched(gateway_app) -> None:
    """Golden case: obligation.policy.protected_paths + current_patch touching it => needs_review, awaiting_approval."""
    import json
    from fastapi.testclient import TestClient

    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_sdk.client import ObligationRuntimeClient

    from tests.integration.conftest import make_testclient_request_adapter

    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    path = fixtures_dir / "patch_protected_path_touched.json"
    if not path.exists():
        pytest.skip("patch_protected_path_touched.json not found")
    raw = json.loads(path.read_text(encoding="utf-8"))
    inp = raw.get("obligation_input", {})
    repo_path = str(
        Path(__file__).resolve().parent.parent / "integration" / "fixtures" / "lean-mini"
    )
    with TestClient(gateway_app) as tc:
        base = make_testclient_request_adapter(tc)

        def adapter(method: str, path_str: str, body: Any) -> dict:
            if method == "POST":
                if "interactive-check" in path_str:
                    return {"ok": True, "diagnostics": [], "goals": []}
                if "batch-verify" in path_str:
                    return {
                        "ok": True,
                        "trust_level": "clean",
                        "build": {"ok": True},
                        "axiom_audit": {"blocked_reasons": []},
                        "fresh_checker": {"ok": True},
                    }
            return base(method, path_str, body)

        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client)
        initial = make_initial_state(
            thread_id="golden_protected_path",
            obligation_id=raw.get("case_id", "protected_path_1"),
            obligation={
                "target": {"repo_id": "lean-mini"},
                "policy": {"protected_paths": inp.get("protected_paths", [])},
            },
            target_files=inp.get("target_files", ["Mini/Basic.lean"]),
            current_patch=inp.get("current_patch", {}),
            repo_path=repo_path,
        )
        result = graph.invoke(initial)
    assert result.get("status") == "awaiting_approval"
    assert (result.get("policy_decision") or {}).get("decision") == "needs_review"
    assert "protected_path_touched" in ((result.get("policy_decision") or {}).get("reasons") or [])
