"""Integration tests for LangChain tools against the Lean Gateway (TestClient).

Validates that the toolset (open_environment, create_session, apply_patch,
check_interactive, batch_verify, etc.) correctly drives the Gateway API and returns
the expected shapes. This is the LangChain integration test: tools are the execution
boundary for agents; this test ensures the same flow as CLI/SDK (open -> session ->
apply -> interactive check -> batch verify) works via tools. See docs/workflow.md
(LangChain integration and tests mapping).
"""

from pathlib import Path
from typing import Any

from obligation_runtime_sdk.client import ObligationRuntimeClient
from obligation_runtime_tools.toolset import build_toolset


def test_tools_e2e_against_gateway(sdk_client: ObligationRuntimeClient) -> None:
    """Tools open_environment, create_session, apply_patch, check_interactive, batch_verify return expected structure."""
    tools = build_toolset("http://testserver", client=sdk_client)
    assert len(tools) >= 5
    open_tool, create_tool, apply_tool, check_tool, batch_tool = (
        tools[0], tools[1], tools[2], tools[3], tools[7]
    )

    def invoke(tool, **kwargs: Any) -> dict:
        if hasattr(tool, "invoke"):
            return tool.invoke(kwargs)
        return tool(**kwargs)

    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_data = invoke(open_tool, repo_id="lean-mini", repo_path=str(repo_path), commit_sha="head")
    assert "fingerprint_id" in open_data
    fingerprint_id = open_data["fingerprint_id"]

    session_data = invoke(create_tool, fingerprint_id=fingerprint_id)
    assert "session_id" in session_data
    session_id = session_data["session_id"]

    apply_data = invoke(apply_tool, session_id=session_id, files={"Mini/Basic.lean": "def x := 1\n"})
    assert "ok" in apply_data

    check_data = invoke(check_tool, session_id=session_id, file_path="Mini/Basic.lean")
    assert "ok" in check_data
    assert "diagnostics" in check_data

    batch_data = invoke(
        batch_tool,
        session_id=session_id,
        target_files=["Mini/Basic.lean"],
        target_declarations=[],
    )
    assert "ok" in batch_data
    assert "trust_level" in batch_data
    assert "reasons" in batch_data
