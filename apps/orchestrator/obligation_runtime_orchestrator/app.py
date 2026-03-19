"""CLI entrypoint: run patch-admissibility graph with gateway URL and optional fixture."""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrator: run patch-admissibility graph (demo or one-shot)."
    )
    parser.add_argument(
        "--gateway",
        default=os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000"),
        help="Gateway base URL (env: OBR_GATEWAY_URL)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "demo"],
        default="run",
        help="run: one-shot; demo: run sample_workflow",
    )
    args = parser.parse_args()
    if args.command == "demo":
        from obligation_runtime_orchestrator.pilot.sample_workflow import (
            run_sample_workflow,
        )

        return run_sample_workflow(gateway_base_url=args.gateway)
    from obligation_runtime_orchestrator.runtime.graph import (
        build_patch_admissibility_graph,
    )
    from obligation_runtime_orchestrator.runtime.state import ObligationRuntimeState

    graph = build_patch_admissibility_graph(gateway_base_url=args.gateway)
    initial: ObligationRuntimeState = {
        "thread_id": "cli-run-1",
        "obligation_id": "ob-cli-1",
        "environment_fingerprint": {},
        "session_id": None,
        "obligation": {},
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
    config = {"configurable": {"thread_id": "cli-run-1"}}
    try:
        for event in graph.stream(initial, config=config):
            for _node, out in event.items():
                if isinstance(out, dict) and out.get("status"):
                    print(out.get("status", ""), flush=True)
        print("done", flush=True)
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
