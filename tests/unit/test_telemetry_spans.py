"""Unit tests: graph emits span events when tracer is provided."""

from __future__ import annotations

import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

try:
    from lean_langchain_telemetry.tracer import InMemoryTracer
except ImportError:
    InMemoryTracer = None


@pytest.mark.skipif(
    StateGraph is None or InMemoryTracer is None,
    reason="langgraph or lean_langchain_telemetry not installed",
)
def test_graph_emits_span_events_with_tracer(gateway_app) -> None:
    """Build graph with InMemoryTracer; invoke; assert node_enter/node_exit events emitted."""
    from fastapi.testclient import TestClient

    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_sdk.client import ObligationRuntimeClient

    from tests.integration.conftest import make_testclient_request_adapter

    from lean_langchain_orchestrator.runtime.initial_state import make_initial_state

    tracer = InMemoryTracer()
    with TestClient(gateway_app) as tc:
        adapter = make_testclient_request_adapter(tc)
        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client, tracer=tracer)
        initial = make_initial_state(
            thread_id="thr_telemetry",
            obligation_id="obl_telemetry",
            obligation={"target": {"repo_id": "lean-mini"}},
            target_files=["Main.lean"],
            repo_path="",
        )
        graph.invoke(initial)
    assert len(tracer.events) >= 2
    enter_events = [e for e in tracer.events if e.event_type == "node_enter"]
    exit_events = [e for e in tracer.events if e.event_type == "node_exit"]
    assert len(enter_events) >= 1
    assert len(exit_events) >= 1
    assert all(e.span_name.startswith("obr.") for e in tracer.events)
    assert all(e.thread_id == "thr_telemetry" for e in tracer.events)


def test_span_by_node_covers_graph_nodes() -> None:
    """SPAN_BY_NODE in graph has an entry for every graph node name (traces cover all nodes)."""
    try:
        from lean_langchain_orchestrator.runtime.graph import SPAN_BY_NODE
    except ImportError:
        pytest.skip("orchestrator not installed")
        return

    graph_node_names = {
        "init_environment",
        "resume_with_approval",
        "retrieve_context",
        "draft_candidate",
        "interactive_check",
        "batch_verify",
        "audit_trust",
        "policy_review",
        "interrupt_for_approval",
        "finalize",
        "repair_from_diagnostics",
        "repair_from_goals",
    }
    for name in graph_node_names:
        assert name in SPAN_BY_NODE, f"SPAN_BY_NODE missing graph node: {name}"
        assert SPAN_BY_NODE[name].startswith("obr."), f"Span name for {name} must start with obr."
