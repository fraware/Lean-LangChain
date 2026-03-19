"""Unit tests: MCP session store restore by session_id and thread_id."""

from __future__ import annotations

from typing import Any

from lean_langchain_orchestrator.mcp_server import (
    MCPSessionContext,
    build_mcp_tools,
)
from lean_langchain_orchestrator.mcp_session_store import InMemoryMCPSessionStore


class _MockClient:
    """Minimal client that records create_session result and apply_patch session_id."""

    def __init__(self) -> None:
        self._session_id = "sess-from-gateway"
        self._apply_patch_session_id: str | None = None

    def open_environment(
        self,
        repo_id: str = "",
        repo_path: str | None = None,
        repo_url: str | None = None,
        commit_sha: str = "HEAD",
    ) -> dict[str, Any]:
        return {"fingerprint_id": "fp1", "repo_id": repo_id}

    def create_session(self, fingerprint_id: str) -> dict[str, Any]:
        return {
            "session_id": self._session_id,
            "fingerprint_id": fingerprint_id,
            "workspace_path": "/workspace",
        }

    def apply_patch(self, session_id: str, files: dict[str, str]) -> dict[str, Any]:
        self._apply_patch_session_id = session_id
        return {"ok": True}

    def interactive_check(self, session_id: str, file_path: str) -> dict[str, Any]:
        return {"ok": True}

    def get_goal(
        self,
        session_id: str,
        file_path: str,
        line: int,
        column: int,
        goal_kind: str = "plainGoal",
    ) -> dict[str, Any]:
        return {"goals": []}

    def batch_verify(
        self,
        session_id: str,
        target_files: list[str],
        target_declarations: list[str],
    ) -> dict[str, Any]:
        return {"ok": True, "build": {"ok": True}}

    def get_review_payload(self, thread_id: str) -> dict[str, Any]:
        return {"thread_id": thread_id}

    def submit_review_decision(self, thread_id: str, decision: str) -> dict[str, Any]:
        return {"decision": "approved"}


def test_restore_by_thread_id_after_simulated_restart() -> None:
    """Create session with thread_id, clear context (simulate restart), call tool with thread_id only; session restored from store."""
    client = _MockClient()
    store = InMemoryMCPSessionStore()
    ctx = MCPSessionContext()

    tools = build_mcp_tools(client, context=ctx, store=store)

    tools["obligation/create_session"](fingerprint_id="fp1", thread_id="thread-abc")
    assert ctx.session_id == "sess-from-gateway"
    assert ctx.thread_id == "thread-abc"

    # Simulate restart: new context, in-memory ctx cleared; store still has the record.
    ctx.clear()
    assert ctx.session_id is None
    assert ctx.thread_id is None

    # Call with thread_id only; should restore from store and use session_id for the API.
    tools["obligation/apply_patch"](thread_id="thread-abc", files={"x.lean": "def a := 1"})

    assert client._apply_patch_session_id == "sess-from-gateway"
    assert ctx.session_id == "sess-from-gateway"
    assert ctx.thread_id == "thread-abc"
