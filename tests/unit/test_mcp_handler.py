"""Unit tests for MCP request handler (in-process, no subprocess)."""

from __future__ import annotations

from lean_langchain_orchestrator.mcp_server_main import handle_mcp_request


def test_mcp_handler_initialize_returns_lean_langchain_server_info() -> None:
    """handle_mcp_request(initialize) returns result with serverInfo.name == lean-langchain."""
    resp = handle_mcp_request("initialize", {}, {})
    assert "result" in resp
    assert "error" not in resp
    result = resp["result"]
    assert result.get("serverInfo", {}).get("name") == "lean-langchain"
    assert result.get("protocolVersion") == "0.1"
    assert "capabilities" in result


def test_mcp_handler_tools_list_returns_expected_tool_names() -> None:
    """handle_mcp_request(tools/list) returns result.tools with expected obligation tool names."""
    resp = handle_mcp_request("tools/list", {}, {})
    assert "result" in resp
    assert "error" not in resp
    tools = resp["result"].get("tools", [])
    names = [t["name"] for t in tools]
    assert "obligation/open_environment" in names
    assert "obligation/create_session" in names
    assert "obligation/apply_patch" in names
    assert "obligation/check_interactive" in names
    assert "obligation/get_goal" in names
    assert "obligation/batch_verify" in names
    assert "obligation/get_review_payload" in names
    assert "obligation/submit_review_decision" in names


def test_mcp_handler_unknown_method_returns_error() -> None:
    """handle_mcp_request(unknown) returns error Method not found."""
    resp = handle_mcp_request("unknown/method", {}, {})
    assert "error" in resp
    assert resp["error"].get("code") == -32601
    assert "Method not found" in (resp["error"].get("message") or "")


def test_mcp_handler_tools_call_unknown_tool_returns_error() -> None:
    """handle_mcp_request(tools/call) with unknown tool name returns error."""
    resp = handle_mcp_request("tools/call", {"name": "nonexistent/tool", "arguments": {}}, {})
    assert "error" in resp
    assert resp["error"].get("code") == -32601
