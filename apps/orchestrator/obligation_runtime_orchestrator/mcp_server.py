"""Persistent MCP adapter: session affinity via thread_id, gateway session_id, environment fingerprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from obligation_runtime_sdk.client import ObligationRuntimeClient


def _sdk_result_to_dict(r: Any) -> dict[str, Any]:
    """Normalize SDK Pydantic models or test doubles (plain dicts) to JSON-shaped dicts."""
    if isinstance(r, dict):
        return dict(r)
    return cast(dict[str, Any], r.model_dump(mode="json"))


@dataclass
class MCPSessionContext:
    """Holds current session for MCP tool calls (session affinity)."""

    session_id: str | None = None
    thread_id: str | None = None
    fingerprint_id: str | None = None
    workspace_path: str | None = None

    def set_from_create_session(
        self, session_id: str, fingerprint_id: str, workspace_path: str = ""
    ) -> None:
        self.session_id = session_id
        self.fingerprint_id = fingerprint_id
        self.workspace_path = workspace_path or None

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """Restore context from a store record."""
        self.session_id = data.get("session_id") or self.session_id
        self.thread_id = data.get("thread_id") or self.thread_id
        self.fingerprint_id = data.get("fingerprint_id") or self.fingerprint_id
        self.workspace_path = data.get("workspace_path") or self.workspace_path

    def clear(self) -> None:
        self.session_id = None
        self.thread_id = None
        self.fingerprint_id = None
        self.workspace_path = None


def build_mcp_tools(
    client: ObligationRuntimeClient,
    context: MCPSessionContext | None = None,
    store: Any = None,
) -> dict[str, Any]:
    """Build MCP tool implementations with optional session context and optional persistent store.
    Keys are tool names (e.g. obligation/open_environment). When store is set, create_session
    persists context and tools can restore from store by session_id when context is empty."""
    ctx = context if context is not None else MCPSessionContext()

    def _maybe_restore(session_id: str | None) -> None:
        if store and session_id and not ctx.session_id:
            loaded = store.get(session_id)
            if loaded:
                ctx.load_from_dict(loaded)

    def open_environment(
        repo_id: str,
        repo_path: str | None = None,
        repo_url: str | None = None,
        commit_sha: str = "HEAD",
    ) -> dict[str, Any]:
        r = client.open_environment(
            repo_id=repo_id, repo_path=repo_path, repo_url=repo_url, commit_sha=commit_sha
        )
        return _sdk_result_to_dict(r)

    def create_session(fingerprint_id: str, thread_id: str | None = None) -> dict[str, Any]:
        if thread_id:
            ctx.thread_id = thread_id
        out = client.create_session(fingerprint_id=fingerprint_id)
        out_d = _sdk_result_to_dict(out)
        session_id = out_d["session_id"]
        fingerprint_id = out_d.get("fingerprint_id", fingerprint_id)
        workspace_path = out_d.get("workspace_path", "")
        ctx.set_from_create_session(
            session_id=session_id, fingerprint_id=fingerprint_id, workspace_path=workspace_path
        )
        if store:
            store.set(
                session_id=session_id,
                thread_id=ctx.thread_id,
                fingerprint_id=fingerprint_id,
                workspace_path=workspace_path,
            )
        return out_d

    def _session_id(session_id: str | None = None, thread_id: str | None = None) -> str:
        # Restore from store by thread_id first (for reconnecting clients), then by session_id.
        if thread_id and not ctx.session_id:
            _maybe_restore(thread_id)
        key = session_id or ctx.session_id
        if key:
            _maybe_restore(key)
        sid = session_id or ctx.session_id
        if not sid:
            raise ValueError(
                "No session_id provided and no session in context. Call obligation/create_session first."
            )
        return sid

    def apply_patch(
        session_id: str | None = None,
        thread_id: str | None = None,
        files: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        r = client.apply_patch(session_id=_session_id(session_id, thread_id), files=files or {})
        return _sdk_result_to_dict(r)

    def check_interactive(
        session_id: str | None = None, thread_id: str | None = None, file_path: str = ""
    ) -> dict[str, Any]:
        r = client.interactive_check(
            session_id=_session_id(session_id, thread_id), file_path=file_path
        )
        return _sdk_result_to_dict(r)

    def get_goal(
        session_id: str | None = None,
        thread_id: str | None = None,
        file_path: str = "",
        line: int = 0,
        column: int = 0,
        goal_kind: str = "plainGoal",
    ) -> dict[str, Any]:
        r = client.get_goal(
            session_id=_session_id(session_id, thread_id),
            file_path=file_path,
            line=line,
            column=column,
            goal_kind=goal_kind,
        )
        return _sdk_result_to_dict(r)

    def batch_verify(
        session_id: str | None = None,
        thread_id: str | None = None,
        target_files: list[str] | None = None,
        target_declarations: list[str] | None = None,
    ) -> dict[str, Any]:
        r = client.batch_verify(
            session_id=_session_id(session_id, thread_id),
            target_files=target_files or [],
            target_declarations=target_declarations or [],
        )
        return _sdk_result_to_dict(r)

    def get_review_payload(thread_id: str) -> dict[str, Any]:
        r = client.get_review_payload(thread_id=thread_id)
        return _sdk_result_to_dict(r)

    def submit_review_decision(thread_id: str, decision: str) -> dict[str, Any]:
        r = client.submit_review_decision(thread_id=thread_id, decision=decision)
        return _sdk_result_to_dict(r)

    def hover(
        session_id: str | None = None,
        thread_id: str | None = None,
        file_path: str = "",
        line: int = 0,
        column: int = 0,
    ) -> dict[str, Any]:
        r = client.hover(
            session_id=_session_id(session_id, thread_id),
            file_path=file_path,
            line=line,
            column=column,
        )
        return _sdk_result_to_dict(r)

    def definition(
        session_id: str | None = None,
        thread_id: str | None = None,
        file_path: str = "",
        line: int = 0,
        column: int = 0,
    ) -> dict[str, Any]:
        r = client.definition(
            session_id=_session_id(session_id, thread_id),
            file_path=file_path,
            line=line,
            column=column,
        )
        return _sdk_result_to_dict(r)

    def resume(thread_id: str) -> dict[str, Any]:
        """Resume the graph after approve/reject. Requires OBR_ORCHESTRATOR_URL on gateway side and checkpointer."""
        r = client.resume(thread_id=thread_id)
        return _sdk_result_to_dict(r)

    return {
        "obligation/open_environment": open_environment,
        "obligation/create_session": create_session,
        "obligation/apply_patch": apply_patch,
        "obligation/check_interactive": check_interactive,
        "obligation/get_goal": get_goal,
        "obligation/batch_verify": batch_verify,
        "obligation/get_review_payload": get_review_payload,
        "obligation/submit_review_decision": submit_review_decision,
        "obligation/hover": hover,
        "obligation/definition": definition,
        "obligation/resume": resume,
    }
