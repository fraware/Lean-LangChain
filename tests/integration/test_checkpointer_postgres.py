"""Integration test for Postgres checkpointer: invoke once, then resume with same thread_id. Skip when no DB."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None

from fastapi.testclient import TestClient

from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
from lean_langchain_orchestrator.runtime.initial_state import make_initial_state
from lean_langchain_sdk.client import ObligationRuntimeClient

from tests.integration.conftest import make_testclient_request_adapter


def _get_postgres_uri() -> str | None:
    uri = os.environ.get("DATABASE_URL")
    return uri if uri else None


@pytest.mark.skipif(
    PostgresSaver is None,
    reason="langgraph-checkpoint-postgres not installed",
)
@pytest.mark.skipif(
    _get_postgres_uri() is None,
    reason="Postgres not configured: set DATABASE_URL",
)
def test_postgres_checkpointer_invoke_then_resume(gateway_app) -> None:
    """Build graph with PostgresSaver, invoke once, then invoke with resume state; assert state restored."""
    uri = _get_postgres_uri()
    assert uri is not None
    saver = PostgresSaver.from_conn_string(uri)
    saver.setup()

    with TestClient(gateway_app) as tc:
        adapter = make_testclient_request_adapter(tc)
        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        graph = build_patch_admissibility_graph(client=client, checkpointer=saver)

        thread_id = "test-checkpointer-postgres-1"
        config = {"configurable": {"thread_id": thread_id}}
        initial = make_initial_state(
            thread_id=thread_id,
            obligation_id="ob-cp-1",
            obligation={"target": {"repo_id": "default"}},
            target_files=["Main.lean"],
            repo_path="",
        )

        result1 = graph.invoke(initial, config=config)
        assert "status" in result1

        resume_state: dict[str, Any] = {
            **initial,
            "approval_required": True,
            "approval_decision": "approved",
            "status": "awaiting_approval",
        }
        result2 = graph.invoke(resume_state, config=config)
        assert "status" in result2
        assert isinstance(result2.get("artifacts"), list)


@pytest.mark.skipif(
    PostgresSaver is None,
    reason="langgraph-checkpoint-postgres not installed",
)
@pytest.mark.skipif(
    _get_postgres_uri() is None,
    reason="Postgres not configured: set DATABASE_URL",
)
def test_postgres_resume_after_interrupt_to_accepted(gateway_app) -> None:
    """Run graph to awaiting_approval (protected path), then resume with approval; assert final status accepted."""
    uri = _get_postgres_uri()
    assert uri is not None
    saver = PostgresSaver.from_conn_string(uri)
    saver.setup()

    with TestClient(gateway_app) as tc:
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
        thread_id = "test-postgres-resume-interrupt"
        config = {"configurable": {"thread_id": thread_id}}
        repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
        protected_path = "Mini/Basic.lean"
        initial = make_initial_state(
            thread_id=thread_id,
            obligation_id="obl-resume-1",
            obligation={
                "target": {"repo_id": "lean-mini"},
                "policy": {"protected_paths": [protected_path]},
            },
            target_files=[protected_path],
            current_patch={protected_path: "def x := 1\n"},
            repo_path=repo_path,
        )
        result1 = graph.invoke(initial, config=config)
        assert result1.get("status") == "awaiting_approval"

        resume_input: dict[str, Any] = {
            **initial,
            "approval_decision": "approved",
            "status": "awaiting_approval",
        }
        result2 = graph.invoke(resume_input, config=config)
        assert result2.get("status") == "accepted"
        assert isinstance(result2.get("artifacts"), list)
