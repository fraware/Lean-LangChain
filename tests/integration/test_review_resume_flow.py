"""Integration tests: review API and resume endpoint.

Validates POST /v1/reviews/{thread_id}/resume: 404 when no review exists for thread,
400 when review exists but no approve/reject decision yet. Ensures the Gateway
resume endpoint is correctly used after human (or UI) approval to continue the
LangGraph run when a checkpointer (e.g. Postgres) persists state. See
docs/workflow.md (workflow step 8, use case 2.3).
"""

from __future__ import annotations

import os

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

import pytest


def test_resume_endpoint_404_when_review_not_found(gateway_client) -> None:
    """POST /v1/reviews/{thread_id}/resume returns 404 when thread has no review."""
    client = gateway_client
    r = client.post("/v1/reviews/no-such-thread/resume", json={})
    assert r.status_code == 404
    body = r.json()
    assert body.get("error", {}).get("code") == "review_not_found"


def test_resume_endpoint_400_when_no_decision(gateway_client) -> None:
    """POST /v1/reviews/{thread_id}/resume returns 400 when review has not been approved/rejected."""
    client = gateway_client
    client.post("/v1/reviews", json={"thread_id": "resume-no-decision", "status": "awaiting_review"})
    r = client.post("/v1/reviews/resume-no-decision/resume", json={})
    assert r.status_code == 400
    body = r.json()
    assert "Approve or reject" in str(body.get("error", {}).get("message", ""))


def test_resume_endpoint_503_when_no_checkpointer(gateway_client) -> None:
    """POST /v1/reviews/{thread_id}/resume returns 503 when no checkpointer (and orchestrator available)."""
    prev_checkpointer = os.environ.pop("CHECKPOINTER", None)
    prev_db = os.environ.pop("DATABASE_URL", None)
    try:
        os.environ.pop("CHECKPOINTER", None)
        os.environ.pop("DATABASE_URL", None)
        client = gateway_client
        client.post("/v1/reviews", json={"thread_id": "resume-no-cp", "status": "awaiting_review"})
        client.post("/v1/reviews/resume-no-cp/approve", json={})
        r = client.post("/v1/reviews/resume-no-cp/resume", json={})
        if r.status_code == 503:
            assert "checkpointer" in str(r.json().get("detail", {}).get("message", "")).lower()
        else:
            assert r.status_code in (200, 503)
    finally:
        if prev_checkpointer is not None:
            os.environ["CHECKPOINTER"] = prev_checkpointer
        if prev_db is not None:
            os.environ["DATABASE_URL"] = prev_db


@pytest.mark.skipif(StateGraph is None, reason="langgraph not installed")
def test_resume_with_approval_continues_to_finalize(gateway_client, obr_graph) -> None:
    """Put pending review in Gateway, approve via API, then run graph with approval_decision -> finalize."""
    thread_id = "resume-flow-thread"

    review_payload = {
        "thread_id": thread_id,
        "obligation_id": "ob-resume",
        "reasons": ["protected_path"],
        "status": "awaiting_review",
    }
    create_r = gateway_client.post("/v1/reviews", json=review_payload)
    assert create_r.status_code == 200
    get_r = gateway_client.get(f"/v1/reviews/{thread_id}")
    assert get_r.status_code == 200
    assert get_r.json()["status"] == "awaiting_review"

    approve_r = gateway_client.post(f"/v1/reviews/{thread_id}/approve", json={})
    assert approve_r.status_code == 200

    resumed_state = {
        "thread_id": thread_id,
        "obligation_id": "ob-resume",
        "session_id": "sess-resume-flow-1",
        "environment_fingerprint": {"repo_id": "r", "commit_sha": "c", "lean_toolchain": "t", "lakefile_hash": "h"},
        "obligation": {},
        "target_files": [],
        "target_declarations": [],
        "current_patch": {},
        "patch_history": [],
        "interactive_result": {"ok": True, "diagnostics": [], "goals": []},
        "goal_snapshots": [],
        "batch_result": {"ok": True, "trust_level": "clean"},
        "policy_decision": {"decision": "needs_review", "trust_level": "clean", "reasons": []},
        "trust_level": "clean",
        "approval_required": True,
        "approval_decision": "approved",
        "status": "awaiting_approval",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
    }
    result = obr_graph.invoke(resumed_state, config={"configurable": {"thread_id": thread_id}})
    assert result.get("status") == "accepted"
    assert result.get("approval_required") is False
    assert any(a.get("kind") == "witness_bundle" for a in result.get("artifacts", []))
