"""Integration tests for the LangGraph patch-admissibility runtime.

Validates the full obligation workflow as implemented by the graph: init_environment
-> retrieve_context -> draft_candidate -> interactive_check -> batch_verify -> audit_trust
-> evaluate_protocol -> policy_review -> (finalize | interrupt_for_approval). Uses
TestClient-backed SDK so no live Gateway is required. Covers: terminal status and
witness bundle on accept; reviewer-gated pack blocking without approval token;
protected-path touch leading to needs_review and awaiting_approval; review payload
containing patch_metadata (e.g. protected_paths_touched). See docs/workflow.md
for workflow, use cases, and the tests-to-integration mapping.
"""

from pathlib import Path
from typing import Any

import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state
from obligation_runtime_policy.constants import REASON_MISSING_APPROVAL_TOKEN
from obligation_runtime_sdk.client import ObligationRuntimeClient

from tests.integration.conftest import make_testclient_request_adapter

_MINIMAL_BATCH_VERIFY_OK: dict[str, Any] = {
    "ok": True,
    "trust_level": "clean",
    "build": {"ok": True, "command": [], "stdout": "", "stderr": "", "timing_ms": 0},
    "axiom_audit": {"ok": True, "trust_level": "clean", "blocked_reasons": []},
    "fresh_checker": {"ok": True, "command": [], "stdout": "", "stderr": "", "timing_ms": 0},
    "reasons": [],
}


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_graph_builds_and_runs_to_terminal(obr_graph) -> None:
    """Build graph with TestClient-backed SDK; run with minimal state; assert terminal and WitnessBundle."""
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="thr_test",
        obligation_id="obl_test",
        obligation={"target": {"repo_id": "lean-mini"}, "environment_fingerprint": {}},
        target_files=["Mini/Basic.lean"],
        current_patch={"Mini/Basic.lean": "def x := 1\n"},
        repo_path=repo_path,
    )
    result = obr_graph.invoke(initial)
    assert "status" in result
    assert result["status"] in (
        "accepted",
        "rejected",
        "failed",
        "awaiting_approval",
        "repairing",
        "auditing",
    )
    if result["status"] == "accepted":
        assert "artifacts" in result
        bundles = [a for a in result["artifacts"] if a.get("kind") == "witness_bundle"]
        assert len(bundles) >= 1
        assert "bundle" in bundles[0]
        b = bundles[0]["bundle"]
        assert "bundle_id" in b
        assert "environment_fingerprint" in b
        assert "policy" in b


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_graph_reviewer_gated_blocks_without_approval_token(obr_graph) -> None:
    """Pack reviewer_gated_execution_v1, no approval_decision => policy_review blocked."""
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="thr_reviewer_gated",
        obligation_id="obl_rg",
        obligation={"target": {"repo_id": "lean-mini"}},
        target_files=["Mini/Basic.lean"],
        repo_path=repo_path,
        policy_pack_name="reviewer_gated_execution_v1",
    )
    result = obr_graph.invoke(initial)
    pd = result.get("policy_decision") or {}
    assert pd.get("decision") == "blocked"
    assert REASON_MISSING_APPROVAL_TOKEN in (pd.get("reasons") or [])


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_graph_protected_path_touched_reaches_needs_review(gateway_tc) -> None:
    """Obligation with policy.protected_paths and current_patch touching it => needs_review."""
    tc = gateway_tc
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: Any) -> dict:
        if method == "POST":
            if "interactive-check" in path:
                return {"ok": True, "diagnostics": [], "goals": []}
            if "batch-verify" in path:
                return dict(_MINIMAL_BATCH_VERIFY_OK)
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    protected_path = "Mini/Basic.lean"
    initial = make_initial_state(
        thread_id="thr_protected",
        obligation_id="obl_prot",
        obligation={
            "target": {"repo_id": "lean-mini"},
            "policy": {"protected_paths": [protected_path]},
        },
        target_files=[protected_path],
        current_patch={protected_path: "def x := 1\n"},
        repo_path=repo_path,
    )
    result = graph.invoke(initial)
    assert result.get("status") == "awaiting_approval"
    pd = result.get("policy_decision") or {}
    assert pd.get("decision") == "needs_review"
    assert "protected_path_touched" in (pd.get("reasons") or [])


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_graph_protected_path_review_payload_has_patch_metadata(gateway_tc) -> None:
    """When protected path is touched, review payload has patch_metadata.protected_paths_touched truthy."""
    tc = gateway_tc
    captured: list[dict] = []
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: Any) -> dict:
        if method == "POST" and path == "/v1/reviews" and body:
            captured.append(body)
        if method == "POST":
            if "interactive-check" in path:
                return {"ok": True, "diagnostics": [], "goals": []}
            if "batch-verify" in path:
                return dict(_MINIMAL_BATCH_VERIFY_OK)
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    protected_path = "Mini/Basic.lean"
    initial = make_initial_state(
        thread_id="thr_capture",
        obligation_id="obl_cap",
        obligation={
            "target": {"repo_id": "lean-mini"},
            "policy": {"protected_paths": [protected_path]},
        },
        target_files=[protected_path],
        current_patch={protected_path: "def x := 1\n"},
        repo_path=repo_path,
    )
    result = graph.invoke(initial)
    assert result.get("status") == "awaiting_approval"
    assert len(captured) >= 1, "create_pending_review should have been called"
    patch_meta = captured[0].get("patch_metadata") or {}
    assert patch_meta.get(
        "protected_paths_touched"
    ), "Review payload patch_metadata.protected_paths_touched should be truthy"
    audit = captured[0].get("policy_audit") or {}
    assert audit.get("policy_pack_name")
    assert isinstance(audit.get("resolved_rules"), list)
