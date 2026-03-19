"""Integration tests for MCP server stdio: list tools and call one (with Gateway or mock)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _send_mcp(
    proc: subprocess.Popen, method: str, params: dict | None = None, msg_id: int = 1
) -> dict:
    req = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        req["params"] = params
    body = json.dumps(req, separators=(",", ":"))
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line.startswith("Content-Length:"):
        return {}
    length = int(line.split(":", 1)[1].strip())
    data = proc.stdout.read(length)
    return json.loads(data)


def test_mcp_server_list_tools() -> None:
    """MCP server responds to initialize and tools/list with obligation tools. Requires install-dev-full."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    orchestrator_dir = repo_root / "apps" / "orchestrator"
    sdk_dir = repo_root / "packages" / "sdk-py"
    schemas_dir = repo_root / "packages" / "schemas"
    env = os.environ.copy()
    env["OBLIGATION_GATEWAY_URL"] = "http://localhost:8000"
    pp = [str(repo_root), str(orchestrator_dir), str(sdk_dir), str(schemas_dir)]
    env["PYTHONPATH"] = os.pathsep.join(pp)
    proc = subprocess.Popen(
        [sys.executable, "-m", "lean_langchain_orchestrator.mcp_server_main"],
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        init_resp = _send_mcp(proc, "initialize", {}, msg_id=1)
        if not init_resp:
            proc.stdin.close()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            stderr = (proc.stderr.read() or "") if proc.stderr else ""
            in_ci = os.environ.get("CI") == "true"
            orchestrator_importable = False
            try:
                __import__("lean_langchain_orchestrator.mcp_server_main")
                orchestrator_importable = True
            except ImportError:
                pass
            if in_ci and orchestrator_importable:
                pytest.fail(f"MCP server did not respond in CI; stderr: {stderr[:500]!r}")
            pytest.skip(f"MCP server no response (run make install-dev-full?): {stderr[:300]}")
        if proc.poll() is not None and "result" not in init_resp:
            stderr = (proc.stderr.read() or "") if proc.stderr else ""
            in_ci = os.environ.get("CI") == "true"
            try:
                __import__("lean_langchain_orchestrator.mcp_server_main")
                orchestrator_importable = True
            except ImportError:
                orchestrator_importable = False
            if in_ci and orchestrator_importable:
                pytest.fail(f"MCP server exited without result in CI; stderr: {stderr[:500]!r}")
            pytest.skip(f"MCP server exited: {stderr[:300]}")
        assert "result" in init_resp, f"Expected result in response: {init_resp}"
        assert init_resp["result"].get("serverInfo", {}).get("name") == "lean-langchain"

        list_resp = _send_mcp(proc, "tools/list", {}, msg_id=2)
        assert "result" in list_resp, f"Expected result in response: {list_resp}"
        tools = list_resp["result"].get("tools", [])
        names = [t["name"] for t in tools]
        assert "obligation/open_environment" in names
        assert "obligation/create_session" in names
        assert "obligation/apply_patch" in names
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
