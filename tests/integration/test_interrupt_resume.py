"""Integration tests for interrupt/resume flow (in-process with MemorySaver).

Validates that when the graph hits needs_review (e.g. protected path touched), it
interrupts and stores state in a checkpointer; a second invoke with the same
thread_id and approval_decision set resumes from resume_with_approval and
reaches finalize. Uses MemorySaver so no Postgres is required; cross-process
resume is covered by test_review_resume_flow and the Gateway resume endpoint.
See docs/workflow.md (LangGraph integration, use case 2.3).
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
from obligation_runtime_sdk.client import ObligationRuntimeClient

from tests.integration.conftest import make_testclient_request_adapter


def _memory_saver():
    try:
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    except ImportError:
        return None


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_resume_in_same_process_with_memory_saver(gateway_tc) -> None:
    """Run graph to interrupt (needs_review), then invoke again with approval_decision.
    Checkpointer restores and finalizes."""
    saver = _memory_saver()
    if saver is None:
        pytest.skip("langgraph checkpoint memory not available")

    tc = gateway_tc
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: Any) -> dict:
        if method == "POST":
            if "interactive-check" in path:
                return {"ok": True, "diagnostics": [], "goals": []}
            if "batch-verify" in path:
                return {
                    "ok": True,
                    "trust_level": "clean",
                    "build": {"ok": True},
                    "axiom_audit": {"blocked_reasons": []},
                    "fresh_checker": {"ok": True},
                }
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client, checkpointer=saver)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    thread_id = "thr_resume_same_process"
    protected_path = "Mini/Basic.lean"
    initial = make_initial_state(
        thread_id=thread_id,
        obligation_id="obl_rsp",
        obligation={
            "target": {"repo_id": "lean-mini"},
            "policy": {"protected_paths": [protected_path]},
        },
        target_files=[protected_path],
        current_patch={protected_path: "def x := 1\n"},
        repo_path=repo_path,
    )
    config = {"configurable": {"thread_id": thread_id}}
    result1 = graph.invoke(initial, config=config)
    assert result1.get("status") == "awaiting_approval"

    resume_state = {
        "thread_id": thread_id,
        "approval_decision": "approved",
    }
    result2 = graph.invoke(resume_state, config=config)
    assert result2.get("status") == "accepted"
    assert any(a.get("kind") == "witness_bundle" for a in result2.get("artifacts", []))


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_resume_with_approval_continues_to_finalize(obr_graph) -> None:
    """State has approval_required and approval_decision=approved;
    graph takes resume path and reaches finalize."""
    resume_state = {
        "thread_id": "thr_resume",
        "obligation_id": "obl_resume",
        "session_id": "sess-resume-test-1",
        "environment_fingerprint": {
            "repo_id": "r",
            "commit_sha": "c",
            "lean_toolchain": "t",
            "lakefile_hash": "h",
        },
        "obligation": {},
        "target_files": [],
        "target_declarations": [],
        "current_patch": {},
        "patch_history": [],
        "interactive_result": {"ok": True, "diagnostics": [], "goals": []},
        "goal_snapshots": [],
        "batch_result": {"ok": True, "trust_level": "clean"},
        "policy_decision": {
            "decision": "needs_review",
            "trust_level": "clean",
            "reasons": [],
        },
        "trust_level": "clean",
        "approval_required": True,
        "approval_decision": "approved",
        "status": "awaiting_approval",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
    }
    result = obr_graph.invoke(resume_state, config={"configurable": {"thread_id": "thr_resume"}})
    assert result.get("status") == "accepted"
    assert result.get("approval_required") is False
    assert any(a.get("kind") == "witness_bundle" for a in result.get("artifacts", []))


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_graph_stream_emits_events_with_minimal_state(gateway_tc) -> None:
    """Graph streams at least one event when invoked with minimal state (open env + session via adapter)."""
    from tests.integration.conftest import make_testclient_request_adapter

    tc = gateway_tc
    adapter = make_testclient_request_adapter(tc)
    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    initial = make_initial_state(
        thread_id="thr_stream_minimal",
        obligation_id="obl_sm",
        obligation={"target": {"repo_id": "lean-mini"}},
        target_files=["Main.lean"],
        repo_path=str(Path(__file__).resolve().parent / "fixtures" / "lean-mini"),
    )
    config = {"configurable": {"thread_id": initial["thread_id"]}}
    events = list(graph.stream(initial, config=config))
    assert len(events) >= 1
    first = events[0]
    assert isinstance(first, dict)
    assert len(first) >= 1
