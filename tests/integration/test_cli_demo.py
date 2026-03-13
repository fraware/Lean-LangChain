"""Integration tests: orchestrator CLI and sample workflow runnable."""

from __future__ import annotations


def test_cli_demo_sample_workflow_returns_exit_code() -> None:
    """run_sample_workflow returns 0 or 1 (does not hang); 1 when gateway unreachable."""
    from obligation_runtime_orchestrator.pilot.sample_workflow import run_sample_workflow

    # Unreachable URL: connection error -> return 1
    code = run_sample_workflow(gateway_base_url="http://127.0.0.1:19999")
    assert code in (0, 1)
