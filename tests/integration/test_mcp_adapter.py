"""Integration tests for MCP adapter: tools list and session affinity."""

from __future__ import annotations


def test_mcp_adapter_tools_list_returns_obligation_tools() -> None:
    """MCP handle_mcp_request(tools/list) returns obligation tool names (get_goal, batch_verify, etc.)."""
    from obligation_runtime_orchestrator.mcp_server_main import handle_mcp_request

    resp = handle_mcp_request("tools/list", {}, {})
    assert "result" in resp
    assert "error" not in resp
    tools = resp["result"].get("tools", [])
    names = [t["name"] for t in tools]
    assert "obligation/get_goal" in names
    assert "obligation/batch_verify" in names
