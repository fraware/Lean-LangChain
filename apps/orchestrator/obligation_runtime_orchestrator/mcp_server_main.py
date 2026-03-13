"""MCP server entrypoint: stdio transport, exposes obligation tools. Set OBLIGATION_GATEWAY_URL to point at the Lean Gateway."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def _read_message() -> dict | None:
    """Read one MCP message from stdin (Content-Length: N + JSON body)."""
    line = sys.stdin.readline()
    if not line:
        return None
    line = line.strip()
    if not line.startswith("Content-Length:"):
        return None
    try:
        length = int(line.split(":", 1)[1].strip())
    except (ValueError, IndexError):
        return None
    body = sys.stdin.read(length)
    return json.loads(body)


def _write_message(msg: dict) -> None:
    """Write one MCP message to stdout."""
    body = json.dumps(msg, separators=(",", ":"))
    sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    sys.stdout.flush()


def _tool_schemas() -> list[dict]:
    """Return MCP tool list schema for obligation tools."""
    return [
        {"name": "obligation/open_environment", "description": "Open a Lean environment by repo_id", "inputSchema": {"type": "object", "properties": {"repo_id": {"type": "string"}, "repo_path": {"type": "string"}, "repo_url": {"type": "string"}, "commit_sha": {"type": "string"}}}},
        {"name": "obligation/create_session", "description": "Create a session for a fingerprint", "inputSchema": {"type": "object", "properties": {"fingerprint_id": {"type": "string"}, "thread_id": {"type": "string"}}}},
        {"name": "obligation/apply_patch", "description": "Apply patch (files) to session", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "thread_id": {"type": "string"}, "files": {"type": "object"}}}},
        {"name": "obligation/check_interactive", "description": "Run interactive check on file", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "thread_id": {"type": "string"}, "file_path": {"type": "string"}}}},
        {"name": "obligation/get_goal", "description": "Get goal at position", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "thread_id": {"type": "string"}, "file_path": {"type": "string"}, "line": {"type": "integer"}, "column": {"type": "integer"}}}},
        {"name": "obligation/batch_verify", "description": "Run batch verification", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "thread_id": {"type": "string"}, "target_files": {"type": "array", "items": {"type": "string"}}, "target_declarations": {"type": "array"}}}},
        {"name": "obligation/get_review_payload", "description": "Get review payload for thread", "inputSchema": {"type": "object", "properties": {"thread_id": {"type": "string"}}}},
        {"name": "obligation/submit_review_decision", "description": "Submit approve/reject for thread", "inputSchema": {"type": "object", "properties": {"thread_id": {"type": "string"}, "decision": {"type": "string"}}}},
    ]


def handle_mcp_request(
    method: str, params: dict[str, Any], tools: dict[str, Any]
) -> dict[str, Any]:
    """Process one MCP request. Returns dict with 'result' or 'error' (JSON-RPC body)."""
    if method == "initialize":
        return {
            "result": {
                "protocolVersion": "0.1",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "obligation-runtime", "version": "0.1.0"},
            }
        }
    if method == "tools/list":
        return {"result": {"tools": _tool_schemas()}}
    if method == "tools/call":
        name = (params.get("name") or "").strip()
        raw_args = params.get("arguments") or {}
        args = dict(raw_args) if isinstance(raw_args, dict) else {}
        if name not in tools:
            return {"error": {"code": -32601, "message": f"Unknown tool: {name}"}}
        try:
            result = tools[name](**args)
            content = [{"type": "text", "text": json.dumps(result)}]
            return {"result": {"content": content}}
        except TypeError as e:
            return {"error": {"code": -32602, "message": f"Invalid arguments: {e}"}}
        except Exception as e:
            return {"error": {"code": -32000, "message": str(e)}}
    err_msg = f"Method not found: {method}"
    return {"error": {"code": -32601, "message": err_msg}}


def _run_server() -> None:
    from obligation_runtime_sdk.client import ObligationRuntimeClient

    from obligation_runtime_orchestrator.mcp_server import (
        MCPSessionContext,
        build_mcp_tools,
    )
    from obligation_runtime_orchestrator.mcp_session_store import get_mcp_session_store

    base_url = os.environ.get("OBLIGATION_GATEWAY_URL", "http://localhost:8000")
    client = ObligationRuntimeClient(base_url=base_url)
    context = MCPSessionContext()
    store = get_mcp_session_store()
    tools = build_mcp_tools(client, context, store=store)

    while True:
        msg = _read_message()
        if msg is None:
            break
        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params") or {}
        response_body = handle_mcp_request(method, params, tools)
        out = {"jsonrpc": "2.0", "id": msg_id, **response_body}
        _write_message(out)


if __name__ == "__main__":
    _run_server()
