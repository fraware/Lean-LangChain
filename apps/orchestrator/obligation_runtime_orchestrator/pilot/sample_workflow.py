"""Sample pilot workflow: run patch-admissibility graph once with minimal fixture."""

from __future__ import annotations

from pathlib import Path


def run_sample_workflow(
    gateway_base_url: str = "http://localhost:8000",
    repo_path: str | Path | None = None,
) -> int:
    """Build graph and run one invocation with fixture state. Returns exit code."""
    from obligation_runtime_orchestrator.runtime.graph import (
        build_patch_admissibility_graph,
    )

    graph = build_patch_admissibility_graph(gateway_base_url=gateway_base_url)
    ob = {"target": {"repo_id": "default"}, "policy": {}, "environment_fingerprint": {}}
    initial: dict = {
        "thread_id": "sample-workflow-1",
        "obligation_id": "ob-sample-1",
        "environment_fingerprint": {},
        "session_id": None,
        "obligation": ob,
        "target_files": ["Main.lean"],
        "target_declarations": [],
        "current_patch": {},
        "patch_history": [],
        "interactive_result": None,
        "goal_snapshots": [],
        "batch_result": None,
        "policy_decision": None,
        "trust_level": None,
        "approval_required": False,
        "approval_decision": None,
        "status": "initialized",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
    }
    if repo_path is not None:
        initial["_repo_path"] = str(Path(repo_path).resolve())

    config = {"configurable": {"thread_id": initial["thread_id"]}}
    try:
        for event in graph.stream(initial, config=config):
            for _node, out in event.items():
                if isinstance(out, dict) and out.get("status"):
                    pass  # caller may log or print
        return 0
    except Exception:
        return 1
