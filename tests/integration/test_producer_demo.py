"""Integration test: run graph with patch from FixturePatchProducer (demo flow). Optional; skip if examples not available."""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

from obligation_runtime_orchestrator.producer import context_from_state
from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state


def _get_fixture_producer():
    try:
        import sys
        repo_root = Path(__file__).resolve().parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from examples.fixture_patch_producer import FixturePatchProducer
        return FixturePatchProducer(constant_patch={"Mini/Basic.lean": "def x := 1\n"})
    except ImportError:
        return None


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_demo_flow_with_fixture_producer(obr_graph) -> None:
    """Fixture producer proposes patch; set current_patch and invoke graph; assert terminal status."""
    producer = _get_fixture_producer()
    if producer is None:
        pytest.skip("examples.fixture_patch_producer not importable")
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="thr_producer_demo",
        obligation_id="obl_demo",
        obligation={"target": {"repo_id": "lean-mini"}, "environment_fingerprint": {}},
        target_files=["Mini/Basic.lean"],
        repo_path=repo_path,
    )
    context = context_from_state(initial)
    patch = producer.propose_patch(context)
    initial["current_patch"] = patch
    result = obr_graph.invoke(initial)
    assert "status" in result
    assert result["status"] in (
        "accepted", "rejected", "failed", "awaiting_approval", "repairing", "auditing",
    )
