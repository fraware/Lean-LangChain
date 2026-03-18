"""Minimal example: build MCP tools that call the Obligation Runtime Gateway.

Run with Gateway up: OBR_GATEWAY_URL=http://localhost:8000 python run_mcp_tools.py
Shows open_environment and create_session; use build_mcp_tools in your own MCP server for full tool list.
"""
from __future__ import annotations

import os

from obligation_runtime_sdk.client import ObligationRuntimeClient
from obligation_runtime_orchestrator.mcp_server import MCPSessionContext, build_mcp_tools

def main() -> None:
    base_url = os.environ.get("OBR_GATEWAY_URL") or os.environ.get("OBLIGATION_GATEWAY_URL", "http://localhost:8000")
    client = ObligationRuntimeClient(base_url=base_url)
    context = MCPSessionContext()
    tools = build_mcp_tools(client, context=context)
    print("Tools:", list(tools.keys()))
    # Example: open environment (no session affinity needed)
    out = tools["obligation/open_environment"](repo_id="default")
    print("open_environment:", out.get("fingerprint_id", out))
    # Create session
    out2 = tools["obligation/create_session"](fingerprint_id=out["fingerprint_id"])
    print("create_session:", out2.get("session_id", out2))

if __name__ == "__main__":
    main()
