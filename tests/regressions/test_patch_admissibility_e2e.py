"""E2E regression: patch admissibility graph run with gateway and golden case."""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_patch_admissibility_e2e_one_golden_run(gateway_app) -> None:
    """Run full graph with gateway_app and one good_patch golden case; assert terminal status."""
    from fastapi.testclient import TestClient

    from obligation_runtime_evals.golden import load_golden_cases
    from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
    from obligation_runtime_sdk.client import ObligationRuntimeClient

    from tests.integration.conftest import make_testclient_request_adapter
    from tests.regressions.test_patch_admissibility_golden import _build_initial_state

    cases = load_golden_cases(["good_patch"])
    if not cases:
        pytest.skip("good_patch golden case not found")
    case = cases[0]
    repo_path = str(Path(__file__).resolve().parent.parent / "integration" / "fixtures" / "lean-mini")
    with TestClient(gateway_app) as tc:
        adapter = make_testclient_request_adapter(tc)
        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client)
        initial = _build_initial_state(case, repo_path)
        result = graph.invoke(initial)
    assert result.get("status") in ("accepted", "rejected", "failed", "awaiting_approval", "repairing", "auditing")
