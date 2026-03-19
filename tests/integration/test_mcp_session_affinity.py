"""Integration tests: MCP adapter preserves session affinity.

Validates that after open_environment and create_session, MCP tools (apply_patch,
check_interactive) use the context session_id when not explicitly passed, so that
session affinity is maintained across tool calls. This is the MCP/LangChain boundary
for the same workflow as test_tools.py but via the MCP server tool build. See
docs/workflow.md (LangChain integration, MCP adapter).
"""

from __future__ import annotations

from pathlib import Path

from obligation_runtime_orchestrator.mcp_server import MCPSessionContext, build_mcp_tools
from obligation_runtime_sdk.client import ObligationRuntimeClient


def test_mcp_session_affinity_apply_and_check_use_context(
    sdk_client: ObligationRuntimeClient,
) -> None:
    """After create_session, apply_patch and check_interactive use context session_id when not passed."""
    ctx = MCPSessionContext()
    tools = build_mcp_tools(sdk_client, context=ctx)

    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_env = tools["obligation/open_environment"](
        repo_id="lean-mini", repo_path=str(repo_path), commit_sha="head"
    )
    fid = open_env["fingerprint_id"]

    tools["obligation/create_session"](fingerprint_id=fid)
    assert ctx.session_id is not None
    assert ctx.fingerprint_id == fid

    apply_out = tools["obligation/apply_patch"](
        session_id=None, files={"Mini/Basic.lean": "def x := 1\n"}
    )
    assert apply_out.get("ok") is True

    check_out = tools["obligation/check_interactive"](session_id=None, file_path="Mini/Basic.lean")
    assert "ok" in check_out


def test_mcp_get_review_payload_and_submit_decision(
    sdk_client: ObligationRuntimeClient, gateway_app
) -> None:
    """get_review_payload and submit_review_decision work when review is pending."""
    from obligation_runtime_lean_gateway.api import deps

    deps.review_store.put(
        "mcp-thread-1", {"thread_id": "mcp-thread-1", "status": "awaiting_review"}
    )
    tools = build_mcp_tools(sdk_client)

    payload = tools["obligation/get_review_payload"](thread_id="mcp-thread-1")
    assert payload["thread_id"] == "mcp-thread-1"

    out = tools["obligation/submit_review_decision"](thread_id="mcp-thread-1", decision="approve")
    assert out.get("decision") == "approved"
